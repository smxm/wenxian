<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { ArrowLeft, RefreshCw, Search } from 'lucide-vue-next'
import {
  NButton,
  NCard,
  NCheckbox,
  NDropdown,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NPagination,
  NSelect,
  NSpin,
  NTag,
  useMessage
} from 'naive-ui'
import {
  applyReviewOverride,
  applySelectionReviewOverride,
  enrichWorkbench as requestEnrichWorkbench,
  fetchTask,
  patchWorkbenchItem as requestPatchWorkbenchItem,
  patchWorkbenchItems as requestPatchWorkbenchItems,
  rebuildWorkbench as requestRebuildWorkbench
} from '@/api/client'
import { useProjectsStore } from '@/stores/projects'
import type {
  ProjectDetail,
  ScreeningRecordRow,
  TaskDetail,
  TaskSnapshot,
  WorkbenchAccessStatus,
  WorkbenchCandidateItem,
  WorkbenchFinalDecision
} from '@/types/api'

type ScreeningDecision = 'include' | 'exclude' | 'uncertain'
type QuickView = 'all' | 'needs-review' | 'review-included' | 'needs-fulltext' | 'fulltext-ready' | 'review-excluded'
type CandidateSort = 'stage' | 'relevance-desc' | 'year-desc' | 'year-asc' | 'updated'
type FulltextStatusFilter = 'all' | 'not-entered' | WorkbenchAccessStatus
type PageSizeOption = 10 | 20 | 50 | 'all'

type ReviewWorkbenchRow = {
  rowId: string
  taskId: string
  taskTitle: string
  roundIndex: number | null
  roundLabel: string
  paperId: string
  title: string
  year?: number | null
  journal?: string | null
  doi?: string | null
  abstract?: string | null
  initialDecision: ScreeningDecision
  initialReason: string
  reviewDecision: ScreeningDecision
  reviewReason: string
  reviewed: boolean
  confidence?: number | string | null
  workbenchItem: WorkbenchCandidateItem | null
  candidateId: string | null
  fulltextStatus: FulltextStatusFilter
  updatedAt: string
}

const route = useRoute()
const router = useRouter()
const message = useMessage()
const projectsStore = useProjectsStore()

const projectId = computed(() => String(route.params.projectId))
const project = computed(() => projectsStore.currentProject)
const workbench = computed(() => project.value?.workbench ?? null)

const screeningTaskDetails = ref<Record<string, TaskDetail>>({})
const loadingScreeningDetails = ref(false)
const loadingTaskIds = ref<Set<string>>(new Set())
const quickView = ref<QuickView>('all')
const searchKeyword = ref('')
const sortMode = ref<CandidateSort>('stage')
const roundFilter = ref<'all' | string>('all')
const screeningFilter = ref<'all' | ScreeningDecision>('all')
const reviewDecisionFilter = ref<'all' | ScreeningDecision>('all')
const fulltextStatusFilter = ref<FulltextStatusFilter>('all')
const yearStart = ref<number | null>(null)
const yearEnd = ref<number | null>(null)
const sourceDatasetIds = ref<string[]>([])
const currentPage = ref(1)
const pageSize = ref<PageSizeOption>(10)
const selectedRowIds = ref<string[]>([])
const activeRowId = ref<string | null>(null)
const showRangeSelectModal = ref(false)
const rangeSelectionStart = ref<number | null>(null)
const rangeSelectionEnd = ref<number | null>(null)
const reviewSubmitting = ref(false)
const workbenchSubmitting = ref(false)
const rebuildingWorkbench = ref(false)
const enrichingWorkbench = ref(false)
const currentCalendarYear = dayjs().year()

const screeningDecisionOptions = [
  { label: '全部初筛建议', value: 'all' },
  { label: '纳入', value: 'include' },
  { label: '剔除', value: 'exclude' },
  { label: '不确定', value: 'uncertain' }
]

const reviewDecisionOptions = [
  { label: '全部复核决定', value: 'all' },
  { label: '纳入全文候选', value: 'include' },
  { label: '排除', value: 'exclude' },
  { label: '待定', value: 'uncertain' }
]

const fulltextStatusOptions = [
  { label: '全部全文状态', value: 'all' },
  { label: '未进入全文', value: 'not-entered' },
  { label: '待获取全文', value: 'pending' },
  { label: '已获取全文', value: 'ready' },
  { label: '无权限', value: 'unavailable' },
  { label: '暂缓', value: 'deferred' }
]

const sortOptions = [
  { label: '按阶段优先', value: 'stage' },
  { label: '按相关度从高到低', value: 'relevance-desc' },
  { label: '按年份从新到旧', value: 'year-desc' },
  { label: '按年份从旧到新', value: 'year-asc' },
  { label: '按最近更新', value: 'updated' }
]

const pageSizeOptions = [
  { label: '10', value: 10 },
  { label: '20', value: 20 },
  { label: '50', value: 50 },
  { label: '全部', value: 'all' }
]

function hasScreeningRoundResults(task: TaskSnapshot) {
  if (task.kind !== 'screening') return false
  const processedCount = Number(task.summary?.processed_count ?? 0)
  const includedCount = Number(task.summary?.included_count ?? 0)
  return task.output_dataset_ids.length > 0 || processedCount > 0 || includedCount > 0
}

function isTemporaryScreeningRound(task: TaskSnapshot) {
  return task.kind === 'screening' && task.status === 'cancelled' && hasScreeningRoundResults(task)
}

function screeningRoundStatusSuffix(task: TaskSnapshot) {
  if (isTemporaryScreeningRound(task)) return ' · 暂存'
  if (task.kind === 'screening' && task.status === 'failed' && hasScreeningRoundResults(task)) return ' · 异常暂存'
  return ''
}

function compactRoundTitle(title: string, maxLength = 22) {
  const normalized = title.trim()
  if (normalized.length <= maxLength) return normalized
  return `${normalized.slice(0, maxLength)}…`
}

const screeningRounds = computed(() =>
  [...(project.value?.tasks ?? [])]
    .filter((task) => hasScreeningRoundResults(task))
    .sort((left, right) => dayjs(right.created_at).valueOf() - dayjs(left.created_at).valueOf())
)

const screeningRoundOrder = computed(() =>
  [...(project.value?.tasks ?? [])]
    .filter((task) => hasScreeningRoundResults(task))
    .sort((left, right) => dayjs(left.created_at).valueOf() - dayjs(right.created_at).valueOf())
)

const screeningTaskMap = computed(() => new Map(screeningRoundOrder.value.map((task) => [task.id, task])))

const roundFilterOptions = computed(() => [
  { label: '全部轮次', value: 'all' },
  ...screeningRounds.value.map((task) => {
    const roundIndex = screeningRoundOrder.value.findIndex((item) => item.id === task.id) + 1
    return {
      label: `第 ${roundIndex} 轮 · ${compactRoundTitle(task.title)}${screeningRoundStatusSuffix(task)}`,
      value: task.id
    }
  })
])

const workbenchSourceOptions = computed(() => {
  const options: Array<{ label: string; value: string }> = []
  for (const dataset of project.value?.datasets ?? []) {
    if (!['cumulative_included', 'included_reviewed', 'included'].includes(dataset.kind)) continue
    options.push({
      label: `${dataset.label} · ${dataset.record_count ?? '-'} 篇`,
      value: dataset.id
    })
  }
  return options
})

const normalizedYearBounds = computed(() => {
  const start = yearStart.value
  const end = yearEnd.value
  if (start !== null && end !== null) return { start: Math.min(start, end), end: Math.max(start, end) }
  return { start, end }
})

const workbenchItems = computed(() => workbench.value?.items ?? [])

function normalizeDecision(value?: string | null): ScreeningDecision {
  if (value === 'include' || value === 'exclude' || value === 'uncertain') return value
  return 'uncertain'
}

function normalizedTitle(value?: string | null) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\u4e00-\u9fff]+/gu, '')
}

function normalizedDoi(value?: string | null) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .replace(/^https?:\/\/(?:dx\.)?doi\.org\//, '')
}

function matchKeysForValues(title?: string | null, doi?: string | null, year?: number | string | null, journal?: string | null) {
  const keys: string[] = []
  const doiKey = normalizedDoi(doi)
  if (doiKey) keys.push(`doi:${doiKey}`)
  const titleKey = normalizedTitle(title)
  const yearKey = year !== null && year !== undefined && year !== '' ? String(year).trim() : ''
  const journalKey = normalizedTitle(journal)
  if (titleKey && yearKey) keys.push(`title-year:${titleKey}|${yearKey}`)
  if (titleKey && journalKey) keys.push(`title-journal:${titleKey}|${journalKey}`)
  if (titleKey) keys.push(`title:${titleKey}`)
  return keys
}

const workbenchByScreeningRef = computed(() => {
  const map = new Map<string, WorkbenchCandidateItem>()
  for (const item of workbenchItems.value) {
    for (const event of item.screening_history ?? []) {
      if (event.task_id && event.paper_id) map.set(`${event.task_id}::${event.paper_id}`, item)
    }
    for (const ref of item.source_record_refs ?? []) {
      if (ref.task_id && ref.paper_id) map.set(`${ref.task_id}::${ref.paper_id}`, item)
    }
  }
  return map
})

const workbenchByMatchKey = computed(() => {
  const map = new Map<string, WorkbenchCandidateItem>()
  for (const item of workbenchItems.value) {
    for (const key of matchKeysForValues(item.title, item.doi, item.year, item.journal)) {
      if (!map.has(key)) map.set(key, item)
    }
  }
  return map
})

function workbenchItemForRecord(taskId: string, record: ScreeningRecordRow) {
  const direct = workbenchByScreeningRef.value.get(`${taskId}::${record.paper_id}`)
  if (direct) return direct
  for (const key of matchKeysForValues(record.title, record.doi, record.year, record.journal)) {
    const matched = workbenchByMatchKey.value.get(key)
    if (matched) return matched
  }
  return null
}

function roundLabel(taskId: string) {
  const task = screeningTaskMap.value.get(taskId)
  const roundIndex = screeningRoundOrder.value.findIndex((item) => item.id === taskId) + 1
  if (!task) return roundIndex > 0 ? `第 ${roundIndex} 轮` : '未关联轮次'
  return `第 ${roundIndex} 轮 · ${compactRoundTitle(task.title)}${screeningRoundStatusSuffix(task)}`
}

function reviewStatusForRow(reviewDecision: ScreeningDecision, item: WorkbenchCandidateItem | null): FulltextStatusFilter {
  if (reviewDecision !== 'include') return 'not-entered'
  return item?.access_status ?? 'pending'
}

const reviewRows = computed<ReviewWorkbenchRow[]>(() => {
  const rows: ReviewWorkbenchRow[] = []
  for (const task of screeningRoundOrder.value) {
    const detail = screeningTaskDetails.value[task.id]
    if (!detail?.records?.length) continue
    const roundIndex = screeningRoundOrder.value.findIndex((item) => item.id === task.id) + 1
    for (const record of detail.records) {
      const item = workbenchItemForRecord(task.id, record)
      const initialDecision = normalizeDecision(record.original_decision ?? record.decision)
      const reviewDecision = normalizeDecision(record.review_decision ?? record.decision)
      rows.push({
        rowId: `${task.id}::${record.paper_id}`,
        taskId: task.id,
        taskTitle: task.title,
        roundIndex: roundIndex > 0 ? roundIndex : null,
        roundLabel: roundLabel(task.id),
        paperId: record.paper_id,
        title: record.title,
        year: record.year,
        journal: record.journal,
        doi: record.doi,
        abstract: record.abstract,
        initialDecision,
        initialReason: record.original_reason ?? record.reason ?? '',
        reviewDecision,
        reviewReason: record.review_reason ?? record.reason ?? '',
        reviewed: Boolean(record.reviewed),
        confidence: record.confidence,
        workbenchItem: item,
        candidateId: item?.candidate_id ?? null,
        fulltextStatus: reviewStatusForRow(reviewDecision, item),
        updatedAt: item?.updated_at ?? detail.updated_at ?? task.updated_at
      })
    }
  }
  return rows
})

const rowMap = computed(() => new Map(reviewRows.value.map((row) => [row.rowId, row])))
const selectedRowIdSet = computed(() => new Set(selectedRowIds.value))
const selectedRows = computed(() =>
  selectedRowIds.value
    .map((rowId) => rowMap.value.get(rowId))
    .filter((row): row is ReviewWorkbenchRow => Boolean(row))
)
const activeRow = computed(() => (activeRowId.value ? rowMap.value.get(activeRowId.value) ?? null : null))

function confidenceNumber(value?: number | string | null) {
  if (value === null || value === undefined || value === '') return null
  if (typeof value === 'number') return Number.isFinite(value) ? (value <= 1 ? value : value / 100) : null
  const parsed = Number(String(value).trim().replace('%', ''))
  if (!Number.isFinite(parsed)) return null
  return parsed <= 1 ? parsed : parsed / 100
}

function confidenceLabel(value?: number | string | null) {
  const normalized = confidenceNumber(value)
  return normalized === null ? null : `${Math.round(normalized * 100)}%`
}

function screeningDecisionLabel(decision: ScreeningDecision) {
  if (decision === 'include') return '纳入'
  if (decision === 'exclude') return '剔除'
  return '不确定'
}

function reviewDecisionLabel(decision: ScreeningDecision) {
  if (decision === 'include') return '纳入全文候选'
  if (decision === 'exclude') return '排除'
  return '待定'
}

function decisionTagType(decision: ScreeningDecision) {
  if (decision === 'include') return 'success'
  if (decision === 'exclude') return 'error'
  return 'warning'
}

function fulltextStatusLabel(status: FulltextStatusFilter) {
  if (status === 'ready') return '已获取全文'
  if (status === 'unavailable') return '无权限'
  if (status === 'deferred') return '暂缓'
  if (status === 'not-entered') return '未进入全文'
  return '待获取全文'
}

function fulltextStatusTagType(status: FulltextStatusFilter) {
  if (status === 'ready') return 'success'
  if (status === 'unavailable') return 'error'
  if (status === 'deferred') return 'warning'
  return undefined
}

function canPatchFulltext(row: ReviewWorkbenchRow) {
  return row.reviewDecision === 'include' && Boolean(row.candidateId)
}

function stageRank(row: ReviewWorkbenchRow) {
  if (row.reviewDecision === 'uncertain') return 0
  if (row.reviewDecision === 'include' && row.fulltextStatus === 'pending') return 1
  if (row.fulltextStatus === 'deferred') return 2
  if (row.fulltextStatus === 'unavailable') return 3
  if (row.fulltextStatus === 'ready') return 4
  if (row.reviewDecision === 'exclude') return 5
  return 6
}

function compareByRelevance(left: ReviewWorkbenchRow, right: ReviewWorkbenchRow) {
  const leftConfidence = confidenceNumber(left.confidence) ?? -1
  const rightConfidence = confidenceNumber(right.confidence) ?? -1
  if (leftConfidence !== rightConfidence) return rightConfidence - leftConfidence
  const leftYear = left.year ?? -Infinity
  const rightYear = right.year ?? -Infinity
  if (leftYear !== rightYear) return rightYear - leftYear
  return left.title.localeCompare(right.title)
}

const filteredRows = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return reviewRows.value
    .filter((row) => {
      if (quickView.value === 'needs-review' && row.reviewDecision !== 'uncertain') return false
      if (quickView.value === 'review-included' && row.reviewDecision !== 'include') return false
      if (quickView.value === 'needs-fulltext' && !(row.reviewDecision === 'include' && row.fulltextStatus === 'pending')) return false
      if (quickView.value === 'fulltext-ready' && row.fulltextStatus !== 'ready') return false
      if (quickView.value === 'review-excluded' && row.reviewDecision !== 'exclude') return false
      if (roundFilter.value !== 'all' && row.taskId !== roundFilter.value) return false
      if (screeningFilter.value !== 'all' && row.initialDecision !== screeningFilter.value) return false
      if (reviewDecisionFilter.value !== 'all' && row.reviewDecision !== reviewDecisionFilter.value) return false
      if (fulltextStatusFilter.value !== 'all' && row.fulltextStatus !== fulltextStatusFilter.value) return false
      if (normalizedYearBounds.value.start !== null || normalizedYearBounds.value.end !== null) {
        if (row.year === null || row.year === undefined) return false
        if (normalizedYearBounds.value.start !== null && row.year < normalizedYearBounds.value.start) return false
        if (normalizedYearBounds.value.end !== null && row.year > normalizedYearBounds.value.end) return false
      }
      if (!keyword) return true
      const haystack = [
        row.title,
        row.journal,
        row.doi,
        row.year,
        row.initialReason,
        row.reviewReason,
        row.roundLabel,
        row.abstract
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(keyword)
    })
    .slice()
    .sort((left, right) => {
      if (sortMode.value === 'relevance-desc') return compareByRelevance(left, right)
      if (sortMode.value === 'updated') return dayjs(right.updatedAt).valueOf() - dayjs(left.updatedAt).valueOf()
      if (sortMode.value === 'year-desc') {
        const leftYear = left.year ?? -Infinity
        const rightYear = right.year ?? -Infinity
        if (leftYear !== rightYear) return rightYear - leftYear
        return compareByRelevance(left, right)
      }
      if (sortMode.value === 'year-asc') {
        const leftYear = left.year ?? Infinity
        const rightYear = right.year ?? Infinity
        if (leftYear !== rightYear) return leftYear - rightYear
        return compareByRelevance(left, right)
      }
      const leftStage = stageRank(left)
      const rightStage = stageRank(right)
      if (leftStage !== rightStage) return leftStage - rightStage
      return compareByRelevance(left, right)
    })
})

const workspaceCounts = computed(() => {
  const counts = {
    total: reviewRows.value.length,
    needsReview: 0,
    reviewIncluded: 0,
    needsFulltext: 0,
    fulltextReady: 0,
    reviewExcluded: 0
  }
  for (const row of reviewRows.value) {
    if (row.reviewDecision === 'uncertain') counts.needsReview += 1
    if (row.reviewDecision === 'include') counts.reviewIncluded += 1
    if (row.reviewDecision === 'include' && row.fulltextStatus === 'pending') counts.needsFulltext += 1
    if (row.fulltextStatus === 'ready') counts.fulltextReady += 1
    if (row.reviewDecision === 'exclude') counts.reviewExcluded += 1
  }
  return counts
})

const quickViewOptions = computed<Array<{ key: QuickView; label: string; count: number }>>(() => [
  { key: 'all', label: '全部初筛结果', count: workspaceCounts.value.total },
  { key: 'needs-review', label: '待人工复核', count: workspaceCounts.value.needsReview },
  { key: 'review-included', label: '复核纳入', count: workspaceCounts.value.reviewIncluded },
  { key: 'needs-fulltext', label: '待获取全文', count: workspaceCounts.value.needsFulltext },
  { key: 'fulltext-ready', label: '已获取全文', count: workspaceCounts.value.fulltextReady },
  { key: 'review-excluded', label: '已排除', count: workspaceCounts.value.reviewExcluded }
])

const effectivePageSize = computed(() => (pageSize.value === 'all' ? Math.max(filteredRows.value.length, 1) : pageSize.value))
const pageCount = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / effectivePageSize.value)))
const currentPageStartIndex = computed(() => (filteredRows.value.length ? (currentPage.value - 1) * effectivePageSize.value + 1 : 0))
const currentPageEndIndex = computed(() => Math.min(currentPage.value * effectivePageSize.value, filteredRows.value.length))
const currentPageRows = computed(() => {
  if (pageSize.value === 'all') return filteredRows.value
  const startIndex = (currentPage.value - 1) * effectivePageSize.value
  return filteredRows.value.slice(startIndex, startIndex + effectivePageSize.value)
})
const currentPageRangeLabel = computed(() =>
  currentPageRows.value.length ? `${currentPageStartIndex.value}-${currentPageEndIndex.value}` : '0-0'
)

const multiSelectOptions = computed(() => [
  {
    label: `当前页全部（第 ${currentPageRangeLabel.value} 条，共 ${currentPageRows.value.length} 篇）`,
    key: 'current-page',
    disabled: !currentPageRows.value.length
  },
  {
    label: `当前筛选全部（${filteredRows.value.length} 篇）`,
    key: 'all-filtered',
    disabled: !filteredRows.value.length
  },
  {
    label: '自定义范围…',
    key: 'range',
    disabled: !filteredRows.value.length
  },
  {
    label: '清空勾选',
    key: 'clear',
    disabled: !selectedRowIds.value.length
  }
])

const selectedFulltextRows = computed(() => selectedRows.value.filter((row) => canPatchFulltext(row)))
const selectedSkippedFulltextCount = computed(() => selectedRows.value.length - selectedFulltextRows.value.length)
function rowPreferredUrl(row: ReviewWorkbenchRow) {
  return row.workbenchItem?.preferred_open_url
    || row.workbenchItem?.preferred_pdf_url
    || (row.doi ? `https://doi.org/${row.doi}` : null)
}

const selectedOpenUrls = computed(() =>
  Array.from(
    new Set(
      selectedRows.value
        .map((row) => rowPreferredUrl(row))
        .filter((url): url is string => Boolean(url))
    )
  )
)
const activeLinks = computed(() => {
  const row = activeRow.value
  if (!row?.workbenchItem) return []
  return row.workbenchItem.links.filter((link) => link.url)
})

function initializeWorkbenchState() {
  sourceDatasetIds.value = [...(workbench.value?.source_dataset_ids ?? [])]
}

function initializeSelection() {
  const validIds = new Set(reviewRows.value.map((row) => row.rowId))
  selectedRowIds.value = selectedRowIds.value.filter((rowId) => validIds.has(rowId))
  if (activeRowId.value && !validIds.has(activeRowId.value)) activeRowId.value = null
}

function applyRouteIntent() {
  const requestedStage = typeof route.query.stage === 'string' ? route.query.stage : null
  const requestedWorkflow = typeof route.query.workflow === 'string' ? route.query.workflow : null
  const requestedTaskId = typeof route.query.screeningTaskId === 'string' ? route.query.screeningTaskId : null
  const validTaskIds = new Set(screeningRounds.value.map((item) => item.id))
  if (requestedStage === 'report-included' || requestedStage === 'ready-for-decision' || requestedWorkflow === 'report-included') {
    quickView.value = 'fulltext-ready'
  }
  if (requestedStage === 'report-excluded') quickView.value = 'review-excluded'
  if (requestedTaskId && validTaskIds.has(requestedTaskId)) roundFilter.value = requestedTaskId
}

async function replaceRouteState() {
  await router.replace({
    query: {
      ...route.query,
      screeningTaskId: roundFilter.value === 'all' ? undefined : roundFilter.value
    }
  })
}

async function loadScreeningTaskDetails() {
  const tasks = screeningRounds.value
  loadingScreeningDetails.value = true
  loadingTaskIds.value = new Set(tasks.map((task) => task.id))
  try {
    const entries = await Promise.all(
      tasks.map(async (task) => {
        try {
          const detail = await fetchTask(task.id)
          return [task.id, detail] as const
        } catch (error) {
          message.error(extractErrorMessage(error, `第 ${screeningRoundOrder.value.findIndex((item) => item.id === task.id) + 1} 轮加载失败`))
          return null
        }
      })
    )
    screeningTaskDetails.value = Object.fromEntries(entries.filter((entry): entry is readonly [string, TaskDetail] => Boolean(entry)))
  } finally {
    loadingTaskIds.value = new Set()
    loadingScreeningDetails.value = false
    initializeSelection()
  }
}

async function loadProject() {
  await projectsStore.loadProject(projectId.value)
  initializeWorkbenchState()
  applyRouteIntent()
  await loadScreeningTaskDetails()
  initializeSelection()
}

watch(
  projectId,
  async () => {
    quickView.value = 'all'
    searchKeyword.value = ''
    selectedRowIds.value = []
    activeRowId.value = null
    await loadProject()
  },
  { immediate: true }
)

watch(
  () => [route.query.workflow, route.query.stage, route.query.screeningTaskId],
  () => {
    if (!project.value) return
    applyRouteIntent()
  }
)

watch(workbench, () => {
  initializeWorkbenchState()
  initializeSelection()
})

watch(
  [quickView, searchKeyword, sortMode, roundFilter, screeningFilter, reviewDecisionFilter, fulltextStatusFilter, yearStart, yearEnd, pageSize],
  () => {
    currentPage.value = 1
  }
)

watch(
  () => filteredRows.value.length,
  () => {
    if (currentPage.value > pageCount.value) currentPage.value = pageCount.value
    if (!filteredRows.value.length) currentPage.value = 1
  }
)

watch(roundFilter, async () => {
  if (!project.value) return
  await replaceRouteState()
})

function setQuickView(nextView: QuickView) {
  quickView.value = nextView
}

function setActiveRow(rowId: string) {
  activeRowId.value = rowId
}

function toggleRowSelected(rowId: string, checked: boolean) {
  if (checked) {
    if (!selectedRowIdSet.value.has(rowId)) selectedRowIds.value = [...selectedRowIds.value, rowId]
    if (!activeRowId.value) activeRowId.value = rowId
    return
  }
  selectedRowIds.value = selectedRowIds.value.filter((item) => item !== rowId)
}

function selectRowBatch(rowIds: string[]) {
  const uniqueIds = Array.from(new Set(rowIds.filter(Boolean)))
  if (!uniqueIds.length) return
  selectedRowIds.value = Array.from(new Set([...selectedRowIds.value, ...uniqueIds]))
  if (!activeRowId.value || !selectedRowIdSet.value.has(activeRowId.value)) activeRowId.value = uniqueIds[0] ?? null
}

function selectCurrentPageRows() {
  if (!currentPageRows.value.length) return
  selectRowBatch(currentPageRows.value.map((row) => row.rowId))
  message.success(`已选中当前页的 ${currentPageRows.value.length} 篇文献`)
}

function selectAllFilteredRows() {
  if (!filteredRows.value.length) return
  selectRowBatch(filteredRows.value.map((row) => row.rowId))
  message.success(`已选中当前筛选结果的 ${filteredRows.value.length} 篇文献`)
}

function openRangeSelectModal() {
  if (!filteredRows.value.length) return
  rangeSelectionStart.value = currentPageStartIndex.value || 1
  rangeSelectionEnd.value = currentPageEndIndex.value || Math.min(effectivePageSize.value, filteredRows.value.length)
  showRangeSelectModal.value = true
}

function handleMultiSelectAction(key: string | number) {
  if (key === 'current-page') {
    selectCurrentPageRows()
    return
  }
  if (key === 'all-filtered') {
    selectAllFilteredRows()
    return
  }
  if (key === 'range') {
    openRangeSelectModal()
    return
  }
  if (key === 'clear') selectedRowIds.value = []
}

function applyRangeSelection() {
  if (!filteredRows.value.length) return
  if (rangeSelectionStart.value === null || rangeSelectionEnd.value === null) {
    message.warning('请先填写起始条目和结束条目。')
    return
  }
  const normalizedStart = Math.max(1, Math.min(rangeSelectionStart.value, rangeSelectionEnd.value))
  const normalizedEnd = Math.min(filteredRows.value.length, Math.max(rangeSelectionStart.value, rangeSelectionEnd.value))
  const rowIds = filteredRows.value.slice(normalizedStart - 1, normalizedEnd).map((row) => row.rowId)
  if (!rowIds.length) {
    message.warning('这个区间里没有可选文献。')
    return
  }
  selectRowBatch(rowIds)
  showRangeSelectModal.value = false
  message.success(`已选中第 ${normalizedStart}-${normalizedEnd} 条，共 ${rowIds.length} 篇文献`)
}

function clearFilters() {
  quickView.value = 'all'
  searchKeyword.value = ''
  sortMode.value = 'stage'
  roundFilter.value = 'all'
  screeningFilter.value = 'all'
  reviewDecisionFilter.value = 'all'
  fulltextStatusFilter.value = 'all'
  yearStart.value = null
  yearEnd.value = null
  currentPage.value = 1
}

function extractErrorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } } | null)?.response?.data?.detail
  if (typeof detail === 'string' && detail) return detail
  const messageText = (error as { message?: unknown } | null)?.message
  if (typeof messageText === 'string' && messageText) return messageText
  return fallback
}

async function refreshWorkspace() {
  await projectsStore.loadProject(projectId.value)
  initializeWorkbenchState()
  await loadScreeningTaskDetails()
  initializeSelection()
}

async function commitWorkbenchProject(nextProject: ProjectDetail) {
  projectsStore.currentProject = nextProject
  await projectsStore.refreshProjects()
  initializeWorkbenchState()
  await loadScreeningTaskDetails()
  initializeSelection()
}

function reviewReasonForDecision(decision: ScreeningDecision) {
  if (decision === 'include') return '人工复核：纳入全文候选'
  if (decision === 'exclude') return '人工复核：排除'
  return '人工复核：待定'
}

async function setRowReviewDecision(row: ReviewWorkbenchRow, decision: ScreeningDecision) {
  reviewSubmitting.value = true
  try {
    await applyReviewOverride(row.taskId, {
      paper_id: row.paperId,
      decision,
      reason: reviewReasonForDecision(decision)
    })
    await refreshWorkspace()
    message.success(`已将当前文献标记为“${reviewDecisionLabel(decision)}”`)
  } catch (error) {
    message.error(extractErrorMessage(error, '复核决定保存失败'))
  } finally {
    reviewSubmitting.value = false
  }
}

async function setRowsReviewDecision(rows: ReviewWorkbenchRow[], decision: ScreeningDecision) {
  if (!rows.length) return
  reviewSubmitting.value = true
  try {
    const grouped = new Map<string, string[]>()
    for (const row of rows) {
      if (!grouped.has(row.taskId)) grouped.set(row.taskId, [])
      grouped.get(row.taskId)?.push(row.paperId)
    }
    for (const [taskId, paperIds] of grouped.entries()) {
      await applySelectionReviewOverride(taskId, {
        paper_ids: Array.from(new Set(paperIds)),
        decision,
        reason: reviewReasonForDecision(decision)
      })
    }
    await refreshWorkspace()
    message.success(`已批量标记 ${rows.length} 篇为“${reviewDecisionLabel(decision)}”`)
  } catch (error) {
    message.error(extractErrorMessage(error, '批量复核失败'))
  } finally {
    reviewSubmitting.value = false
  }
}

async function patchCandidate(candidateId: string, payload: {
  access_status?: WorkbenchAccessStatus | null
  final_decision?: WorkbenchFinalDecision | null
  access_note?: string | null
  final_note?: string | null
}) {
  if (!project.value) return
  workbenchSubmitting.value = true
  try {
    const updatedProject = await requestPatchWorkbenchItem(project.value.id, candidateId, payload)
    await commitWorkbenchProject(updatedProject)
    message.success('全文状态已保存')
  } catch (error) {
    message.error(extractErrorMessage(error, '全文状态保存失败'))
  } finally {
    workbenchSubmitting.value = false
  }
}

async function patchRowsFulltextStatus(rows: ReviewWorkbenchRow[], status: WorkbenchAccessStatus) {
  if (!project.value || !rows.length) return
  const candidateIds = Array.from(new Set(rows.map((row) => row.candidateId).filter((candidateId): candidateId is string => Boolean(candidateId))))
  if (!candidateIds.length) {
    message.warning('当前勾选里没有已复核纳入的全文候选。')
    return
  }
  workbenchSubmitting.value = true
  try {
    const updatedProject = await requestPatchWorkbenchItems(project.value.id, {
      candidate_ids: candidateIds,
      access_status: status
    })
    await commitWorkbenchProject(updatedProject)
    if (selectedSkippedFulltextCount.value > 0) {
      message.warning(`已处理 ${candidateIds.length} 篇；全文动作只作用于已复核纳入的文献。`)
    } else {
      message.success(`已批量标记 ${candidateIds.length} 篇为“${fulltextStatusLabel(status)}”`)
    }
  } catch (error) {
    message.error(extractErrorMessage(error, '批量全文状态保存失败'))
  } finally {
    workbenchSubmitting.value = false
  }
}

async function rebuildProjectWorkbench() {
  if (!project.value) return
  rebuildingWorkbench.value = true
  try {
    const updatedProject = await requestRebuildWorkbench(project.value.id, { source_dataset_ids: [...sourceDatasetIds.value] })
    await commitWorkbenchProject(updatedProject)
    message.success('全文候选已按当前来源同步')
  } catch (error) {
    message.error(extractErrorMessage(error, '全文候选同步失败'))
  } finally {
    rebuildingWorkbench.value = false
  }
}

async function enrichProjectWorkbench() {
  if (!project.value) return
  enrichingWorkbench.value = true
  try {
    const updatedProject = await requestEnrichWorkbench(project.value.id)
    await commitWorkbenchProject(updatedProject)
    message.success('OA / PDF 链接已刷新')
  } catch (error) {
    message.error(extractErrorMessage(error, '链接刷新失败'))
  } finally {
    enrichingWorkbench.value = false
  }
}

function openExternal(url?: string | null) {
  if (!url) return
  window.open(url, '_blank', 'noopener')
}

function openMany(urls: string[], label: string) {
  if (!urls.length) return
  let blockedCount = 0
  for (const url of urls) {
    const opened = window.open(url, '_blank', 'noopener')
    if (!opened) blockedCount += 1
  }
  if (blockedCount > 0) {
    message.warning(`已尝试打开 ${urls.length} 个${label}，其中 ${blockedCount} 个可能被浏览器拦截。`)
    return
  }
  message.success(`已打开 ${urls.length} 个${label}`)
}
</script>

<template>
  <div class="review-page">
    <NSpin :show="projectsStore.loadingDetail && !project">
      <div v-if="project" class="review-stack">
        <section class="review-hero">
          <div class="hero-main">
            <div class="eyebrow">Review & Fulltext Workspace</div>
            <h1>复核与全文工作台</h1>
            <p>把初筛建议、人工复核决定和全文获取状态放在同一条文献流里；报告生成时再从已获取全文里选择本次输入。</p>
          </div>
          <div class="hero-actions">
            <RouterLink :to="`/threads/${project.id}`">
              <NButton secondary>
                <template #icon><ArrowLeft :size="16" /></template>
                返回主题页
              </NButton>
            </RouterLink>
          </div>
        </section>

        <section class="overview-strip">
          <div class="overview-item">
            <span>全部初筛结果</span>
            <strong>{{ workspaceCounts.total }}</strong>
          </div>
          <div class="overview-item">
            <span>待人工复核</span>
            <strong>{{ workspaceCounts.needsReview }}</strong>
          </div>
          <div class="overview-item">
            <span>待获取全文</span>
            <strong>{{ workspaceCounts.needsFulltext }}</strong>
          </div>
          <div class="overview-item">
            <span>已获取全文</span>
            <strong>{{ workspaceCounts.fulltextReady }}</strong>
          </div>
          <div class="overview-item">
            <span>已排除</span>
            <strong>{{ workspaceCounts.reviewExcluded }}</strong>
          </div>
        </section>

        <section class="workspace-layout">
          <aside class="filters-sidebar">
            <NCard class="panel-surface filter-panel" embedded>
              <div class="card-title-row sidebar-title-row">
                <div>
                  <div class="section-title">筛选与来源</div>
                  <div class="section-copy">先收窄文献流，再进入单篇或批量处理。</div>
                </div>
                <div class="section-meta">{{ filteredRows.length }} 篇</div>
              </div>

              <div class="filter-panel-stack">
                <div class="filter-section">
                  <div class="filter-section-title">快捷视图</div>
                  <div class="quick-view-stack">
                    <button
                      v-for="item in quickViewOptions"
                      :key="item.key"
                      class="quick-view-button"
                      :class="{ active: quickView === item.key }"
                      type="button"
                      @click="setQuickView(item.key)"
                    >
                      <span>{{ item.label }}</span>
                      <strong>{{ item.count }}</strong>
                    </button>
                  </div>
                </div>

                <div class="filter-section">
                  <div class="filter-section-title">排序</div>
                  <NSelect v-model:value="sortMode" :options="sortOptions" />
                </div>

                <div class="filter-section">
                  <div class="filter-section-title">年份范围</div>
                  <div class="year-range-grid">
                    <NInputNumber v-model:value="yearStart" clearable :show-button="false" :min="1900" :max="currentCalendarYear" placeholder="起始年份" />
                    <NInputNumber v-model:value="yearEnd" clearable :show-button="false" :min="1900" :max="currentCalendarYear" placeholder="结束年份" />
                  </div>
                </div>

                <div class="filter-section">
                  <div class="filter-section-title">来源轮次</div>
                  <NSelect v-model:value="roundFilter" :options="roundFilterOptions" />
                </div>

                <div class="filter-section">
                  <div class="filter-section-title">初筛建议</div>
                  <NSelect v-model:value="screeningFilter" :options="screeningDecisionOptions" />
                </div>

                <div class="filter-section">
                  <div class="filter-section-title">复核决定</div>
                  <NSelect v-model:value="reviewDecisionFilter" :options="reviewDecisionOptions" />
                </div>

                <div class="filter-section">
                  <div class="filter-section-title">全文状态</div>
                  <NSelect v-model:value="fulltextStatusFilter" :options="fulltextStatusOptions" />
                </div>

                <div class="filter-section">
                  <div class="filter-section-title">关键词</div>
                  <NInput v-model:value="searchKeyword" placeholder="搜标题、期刊、DOI、理由或摘要">
                    <template #prefix><Search :size="16" /></template>
                  </NInput>
                </div>

                <div class="filter-section">
                  <div class="filter-section-title">全文来源同步</div>
                  <NForm label-placement="top">
                    <NFormItem label="纳入全文候选的数据集">
                      <NSelect v-model:value="sourceDatasetIds" multiple :options="workbenchSourceOptions" />
                    </NFormItem>
                  </NForm>
                  <div class="toolbar-actions">
                    <NButton type="primary" :loading="rebuildingWorkbench" :disabled="!sourceDatasetIds.length || enrichingWorkbench" @click="rebuildProjectWorkbench">
                      同步全文候选
                    </NButton>
                    <NButton secondary :loading="enrichingWorkbench" :disabled="rebuildingWorkbench" @click="enrichProjectWorkbench">
                      <template #icon><RefreshCw :size="16" /></template>
                      刷新 OA / PDF
                    </NButton>
                  </div>
                </div>

                <div class="filter-actions">
                  <NButton tertiary @click="clearFilters">清空筛选</NButton>
                </div>
              </div>
            </NCard>
          </aside>

          <main class="records-column">
            <NCard class="panel-surface records-card" embedded>
              <div class="card-title-row">
                <div>
                  <div class="section-title">文献候选结果</div>
                  <div class="section-copy">默认每页 10 篇；勾选用于批量处理，点击行用于右侧查看单篇详情。</div>
                </div>
                <div class="section-meta">显示 {{ filteredRows.length }} / {{ reviewRows.length }} 篇</div>
              </div>

              <div class="results-topbar">
                <NDropdown trigger="click" :options="multiSelectOptions" @select="handleMultiSelectAction">
                  <NButton secondary :disabled="!filteredRows.length || reviewSubmitting || workbenchSubmitting">多选</NButton>
                </NDropdown>
                <div class="results-topbar-copy">
                  当前页 {{ currentPageRangeLabel }} · 已勾选 {{ selectedRowIds.length }} 篇
                </div>
              </div>

              <div v-if="selectedRowIds.length" class="selection-toolbar">
                <div class="selection-summary">
                  <strong>已选 {{ selectedRowIds.length }} 篇</strong>
                  <span v-if="selectedSkippedFulltextCount">
                    全文动作只会作用于已复核纳入的 {{ selectedFulltextRows.length }} 篇。
                  </span>
                  <span v-else>可批量复核，也可批量标记全文获取状态。</span>
                </div>
                <div class="selection-actions">
                  <NButton type="success" size="small" :loading="reviewSubmitting" @click="setRowsReviewDecision(selectedRows, 'include')">
                    批量纳入全文候选
                  </NButton>
                  <NButton type="error" size="small" :loading="reviewSubmitting" @click="setRowsReviewDecision(selectedRows, 'exclude')">
                    批量排除
                  </NButton>
                  <NButton type="warning" size="small" :loading="reviewSubmitting" @click="setRowsReviewDecision(selectedRows, 'uncertain')">
                    批量待定
                  </NButton>
                  <NButton secondary size="small" :disabled="!selectedOpenUrls.length" @click="openMany(selectedOpenUrls, '文献链接')">
                    批量打开链接
                  </NButton>
                  <NButton type="success" size="small" :disabled="!selectedFulltextRows.length" :loading="workbenchSubmitting" @click="patchRowsFulltextStatus(selectedFulltextRows, 'ready')">
                    批量标记已获取全文
                  </NButton>
                  <NButton type="error" size="small" :disabled="!selectedFulltextRows.length" :loading="workbenchSubmitting" @click="patchRowsFulltextStatus(selectedFulltextRows, 'unavailable')">
                    批量无权限
                  </NButton>
                  <NButton type="warning" size="small" :disabled="!selectedFulltextRows.length" :loading="workbenchSubmitting" @click="patchRowsFulltextStatus(selectedFulltextRows, 'deferred')">
                    批量暂缓
                  </NButton>
                  <NButton tertiary size="small" @click="selectedRowIds = []">清空勾选</NButton>
                </div>
              </div>

              <NSpin :show="loadingScreeningDetails">
                <div v-if="currentPageRows.length" class="record-list">
                  <article
                    v-for="row in currentPageRows"
                    :key="row.rowId"
                    class="record-row"
                    :class="{ active: activeRowId === row.rowId, selected: selectedRowIdSet.has(row.rowId) }"
                    @click="setActiveRow(row.rowId)"
                  >
                    <div class="record-check">
                      <NCheckbox
                        :checked="selectedRowIdSet.has(row.rowId)"
                        @click.stop
                        @update:checked="(checked) => toggleRowSelected(row.rowId, Boolean(checked))"
                      />
                    </div>
                    <div class="record-main">
                      <div class="record-head">
                        <div class="record-heading-block">
                          <h2>{{ row.title }}</h2>
                          <div class="record-meta" :title="`${row.journal || '未知期刊'} · ${row.roundLabel}`">
                            {{ row.journal || '未知期刊' }} · {{ row.roundLabel }}
                          </div>
                        </div>
                        <div class="record-tags">
                          <NTag round size="small" :type="decisionTagType(row.initialDecision)">初筛 {{ screeningDecisionLabel(row.initialDecision) }}</NTag>
                          <NTag round size="small" :type="decisionTagType(row.reviewDecision)">复核 {{ reviewDecisionLabel(row.reviewDecision) }}</NTag>
                          <NTag round size="small" :type="fulltextStatusTagType(row.fulltextStatus)">{{ fulltextStatusLabel(row.fulltextStatus) }}</NTag>
                          <NTag round size="small">{{ row.year ?? '----' }}</NTag>
                          <NTag v-if="confidenceLabel(row.confidence)" round size="small" type="success">相关度 {{ confidenceLabel(row.confidence) }}</NTag>
                        </div>
                      </div>
                      <div class="record-reason">{{ row.reviewReason || row.initialReason || '暂无筛选理由' }}</div>
                    </div>
                  </article>
                </div>
                <NEmpty
                  v-else
                  class="empty-state"
                  :description="reviewRows.length ? '当前筛选条件下没有匹配文献' : '当前主题还没有可复核的筛选记录'"
                />
              </NSpin>

              <div v-if="filteredRows.length" class="pagination-bar">
                <div class="page-size-control">
                  <span>每页</span>
                  <NSelect v-model:value="pageSize" size="small" :options="pageSizeOptions" class="page-size-select" />
                </div>
                <div class="pagination-copy">
                  第 {{ currentPageStartIndex }}-{{ currentPageEndIndex }} 条 / 共 {{ filteredRows.length }} 条
                </div>
                <NPagination v-if="pageCount > 1" v-model:page="currentPage" :page-count="pageCount" />
              </div>
            </NCard>
          </main>

          <aside class="inspector-sidebar">
            <NCard class="panel-surface inspector-card" embedded>
              <div class="card-title-row">
                <div>
                  <div class="section-title">当前文献</div>
                  <div class="section-copy">点击中间任一文献后，这里显示单篇信息和操作。</div>
                </div>
                <div class="section-meta">
                  <template v-if="selectedRowIds.length">已勾选 {{ selectedRowIds.length }} 篇</template>
                  <template v-else-if="activeRow">{{ reviewDecisionLabel(activeRow.reviewDecision) }}</template>
                  <template v-else>未选择</template>
                </div>
              </div>

              <template v-if="activeRow">
                <div class="active-paper">
                  <h2>{{ activeRow.title }}</h2>
                  <div class="focus-meta">
                    <NTag round size="small" class="round-label-tag">
                      <span class="tag-ellipsis" :title="activeRow.roundLabel">{{ activeRow.roundLabel }}</span>
                    </NTag>
                    <NTag round size="small" :type="decisionTagType(activeRow.initialDecision)">初筛 {{ screeningDecisionLabel(activeRow.initialDecision) }}</NTag>
                    <NTag round size="small" :type="decisionTagType(activeRow.reviewDecision)">复核 {{ reviewDecisionLabel(activeRow.reviewDecision) }}</NTag>
                    <NTag round size="small" :type="fulltextStatusTagType(activeRow.fulltextStatus)">{{ fulltextStatusLabel(activeRow.fulltextStatus) }}</NTag>
                    <NTag v-if="confidenceLabel(activeRow.confidence)" round size="small" type="success">相关度 {{ confidenceLabel(activeRow.confidence) }}</NTag>
                  </div>

                  <div class="action-block">
                    <div class="action-title">单篇复核操作</div>
                    <div class="action-grid">
                      <NButton type="success" :loading="reviewSubmitting" @click="setRowReviewDecision(activeRow, 'include')">纳入全文候选</NButton>
                      <NButton type="error" :loading="reviewSubmitting" @click="setRowReviewDecision(activeRow, 'exclude')">排除</NButton>
                      <NButton type="warning" :loading="reviewSubmitting" @click="setRowReviewDecision(activeRow, 'uncertain')">待定</NButton>
                    </div>
                  </div>

                  <div class="action-block">
                    <div class="action-title">全文获取操作</div>
                    <div v-if="canPatchFulltext(activeRow)" class="action-grid">
                      <NButton secondary :disabled="!activeRow.workbenchItem?.preferred_open_url && !activeRow.workbenchItem?.preferred_pdf_url" @click="openExternal(activeRow.workbenchItem?.preferred_open_url || activeRow.workbenchItem?.preferred_pdf_url)">
                        打开链接
                      </NButton>
                      <NButton tertiary :disabled="!activeRow.workbenchItem?.preferred_pdf_url" @click="openExternal(activeRow.workbenchItem?.preferred_pdf_url)">打开 PDF</NButton>
                      <NButton type="success" :loading="workbenchSubmitting" @click="patchCandidate(activeRow.candidateId!, { access_status: 'ready' })">已获取全文</NButton>
                      <NButton type="error" :loading="workbenchSubmitting" @click="patchCandidate(activeRow.candidateId!, { access_status: 'unavailable' })">无权限</NButton>
                      <NButton type="warning" :loading="workbenchSubmitting" @click="patchCandidate(activeRow.candidateId!, { access_status: 'deferred' })">暂缓</NButton>
                    </div>
                    <p v-else class="hint-line">这篇文献尚未复核纳入全文候选，暂不显示全文状态操作。</p>
                  </div>

                  <div class="detail-grid">
                    <div class="detail-block">
                      <span class="detail-label">来源轮次</span>
                      <strong class="detail-ellipsis" :title="activeRow.roundLabel">{{ activeRow.roundLabel }}</strong>
                    </div>
                    <div class="detail-block">
                      <span class="detail-label">期刊 / 年份</span>
                      <strong>{{ activeRow.journal || '未知期刊' }} · {{ activeRow.year ?? '年份未知' }}</strong>
                    </div>
                    <div class="detail-block">
                      <span class="detail-label">DOI</span>
                      <strong>{{ activeRow.doi || '暂无 DOI' }}</strong>
                    </div>
                    <div class="detail-block">
                      <span class="detail-label">初筛理由</span>
                      <p>{{ activeRow.initialReason || '暂无初筛理由' }}</p>
                    </div>
                    <div class="detail-block">
                      <span class="detail-label">复核决定</span>
                      <p>{{ reviewDecisionLabel(activeRow.reviewDecision) }}{{ activeRow.reviewed ? ' · 已人工复核' : '' }}</p>
                    </div>
                    <div class="detail-block">
                      <span class="detail-label">摘要</span>
                      <p>{{ activeRow.abstract || '暂无摘要' }}</p>
                    </div>
                  </div>

                  <div v-if="activeLinks.length" class="link-stack">
                    <div class="action-title">可打开链接</div>
                    <button v-for="link in activeLinks" :key="`${link.kind}-${link.url}`" class="link-row" type="button" @click="openExternal(link.url)">
                      <span>{{ link.label }}</span>
                      <strong>{{ link.url }}</strong>
                    </button>
                  </div>
                </div>
              </template>

              <NEmpty v-else class="empty-inspector" description="点击中间列表中的文献后，这里会显示单篇详情。" />

              <div v-if="selectedRowIds.length" class="selection-sidecar">
                <div class="action-title">批量操作摘要</div>
                <p>已勾选 {{ selectedRowIds.length }} 篇，其中 {{ selectedFulltextRows.length }} 篇可直接执行全文状态动作。</p>
                <div class="action-grid">
                  <NButton type="success" size="small" :loading="reviewSubmitting" @click="setRowsReviewDecision(selectedRows, 'include')">纳入全文候选</NButton>
                  <NButton type="error" size="small" :loading="reviewSubmitting" @click="setRowsReviewDecision(selectedRows, 'exclude')">排除</NButton>
                  <NButton type="warning" size="small" :loading="reviewSubmitting" @click="setRowsReviewDecision(selectedRows, 'uncertain')">待定</NButton>
                  <NButton secondary size="small" :disabled="!selectedOpenUrls.length" @click="openMany(selectedOpenUrls, '文献链接')">打开链接</NButton>
                </div>
              </div>
            </NCard>
          </aside>
        </section>
      </div>

      <NEmpty v-else class="panel-surface empty-state" description="主题不存在或仍在加载中" />
    </NSpin>

    <NModal v-model:show="showRangeSelectModal" preset="card" title="按区间多选" style="width: 420px" :bordered="false">
      <div class="range-select-modal">
        <p class="range-select-copy">按当前筛选结果的顺序选择条目，例如 1-10、21-30。</p>
        <div class="range-select-grid">
          <NFormItem label="起始条目">
            <NInputNumber v-model:value="rangeSelectionStart" :show-button="false" :min="1" :max="filteredRows.length || 1" placeholder="例如 1" />
          </NFormItem>
          <NFormItem label="结束条目">
            <NInputNumber v-model:value="rangeSelectionEnd" :show-button="false" :min="1" :max="filteredRows.length || 1" placeholder="例如 10" />
          </NFormItem>
        </div>
        <div class="range-select-foot">
          <span>当前可选范围：1-{{ filteredRows.length }}</span>
          <div class="range-select-actions">
            <NButton tertiary @click="showRangeSelectModal = false">取消</NButton>
            <NButton type="primary" @click="applyRangeSelection">应用区间</NButton>
          </div>
        </div>
      </div>
    </NModal>
  </div>
</template>

<style scoped>
.review-page,
.review-stack,
.records-column,
.filter-panel-stack,
.record-list,
.detail-grid,
.active-paper,
.link-stack {
  display: flex;
  flex-direction: column;
}

.review-page,
.review-stack {
  gap: 18px;
}

.review-hero,
.overview-strip,
.records-card,
.filter-panel,
.inspector-card {
  border-radius: 18px;
}

.review-hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 26px 28px;
  background: linear-gradient(135deg, rgba(245, 248, 242, 0.98), rgba(255, 253, 248, 0.98));
  border: 1px solid rgba(97, 113, 91, 0.14);
}

.hero-main h1 {
  margin: 6px 0 10px;
  font-size: 34px;
  line-height: 1.1;
}

.hero-main p {
  margin: 0;
  max-width: 820px;
  color: rgba(56, 53, 44, 0.8);
  line-height: 1.7;
}

.eyebrow {
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(75, 98, 73, 0.74);
}

.hero-actions {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.overview-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  padding: 12px;
  background: rgba(251, 249, 244, 0.78);
  border: 1px solid rgba(97, 113, 91, 0.1);
}

.overview-item {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(97, 113, 91, 0.1);
}

.overview-item span {
  display: block;
  color: rgba(64, 60, 51, 0.68);
  font-size: 13px;
}

.overview-item strong {
  display: block;
  margin-top: 6px;
  font-size: 24px;
  line-height: 1;
}

.workspace-layout {
  display: grid;
  grid-template-columns: minmax(250px, 300px) minmax(0, 1fr) minmax(310px, 380px);
  gap: 16px;
  align-items: start;
}

.filters-sidebar,
.inspector-sidebar {
  position: sticky;
  top: 24px;
  align-self: start;
}

.panel-surface {
  background: rgba(255, 252, 246, 0.94);
  border: 1px solid rgba(97, 113, 91, 0.1);
}

.card-title-row {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
}

.card-title-row > *,
.record-main,
.record-heading-block,
.selection-summary,
.section-copy,
.section-meta,
.results-topbar-copy {
  min-width: 0;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
}

.section-copy,
.detail-block p,
.hint-line,
.record-reason,
.record-meta,
.selection-summary span,
.pagination-copy,
.results-topbar-copy,
.range-select-copy,
.selection-sidecar p {
  color: rgba(64, 60, 51, 0.75);
  line-height: 1.6;
}

.section-meta {
  color: rgba(64, 60, 51, 0.68);
  text-align: right;
  overflow-wrap: anywhere;
}

.filter-panel-stack {
  gap: 16px;
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filter-section + .filter-section {
  padding-top: 16px;
  border-top: 1px solid rgba(97, 113, 91, 0.1);
}

.filter-section-title,
.action-title {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: rgba(54, 70, 53, 0.78);
}

.quick-view-stack {
  display: grid;
  gap: 8px;
}

.quick-view-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(97, 113, 91, 0.14);
  background: rgba(255, 255, 255, 0.86);
  color: #2e2a22;
  cursor: pointer;
}

.quick-view-button.active {
  border-color: rgba(38, 87, 63, 0.36);
  background: rgba(38, 87, 63, 0.1);
}

.year-range-grid,
.range-select-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.toolbar-actions,
.filter-actions,
.selection-actions,
.action-grid,
.range-select-actions,
.results-topbar,
.pagination-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.results-topbar,
.pagination-bar {
  align-items: center;
  justify-content: space-between;
}

.results-topbar {
  padding: 12px 14px;
  margin-bottom: 12px;
  border-radius: 12px;
  background: rgba(247, 244, 236, 0.86);
}

.selection-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 14px;
  border-radius: 14px;
  background: rgba(237, 247, 235, 0.88);
  border: 1px solid rgba(94, 134, 91, 0.18);
}

.selection-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.record-list,
.active-paper,
.detail-grid,
.link-stack {
  gap: 12px;
}

.record-row {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 12px;
  padding: 15px;
  border-radius: 14px;
  border: 1px solid rgba(97, 113, 91, 0.14);
  background: rgba(255, 255, 255, 0.92);
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.record-row:hover,
.record-row.active {
  border-color: rgba(38, 87, 63, 0.38);
  box-shadow: 0 12px 24px rgba(38, 60, 43, 0.08);
  transform: translateY(-1px);
}

.record-row.selected {
  background: rgba(246, 251, 244, 0.96);
}

.record-check {
  padding-top: 4px;
}

.record-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.record-head h2,
.active-paper h2 {
  margin: 0;
  font-size: 17px;
  line-height: 1.35;
}

.record-tags,
.focus-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.record-tags {
  justify-content: flex-end;
}

.record-meta,
.record-reason {
  margin-top: 8px;
}

.record-meta,
.detail-ellipsis,
.tag-ellipsis {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-meta {
  max-width: 100%;
}

.round-label-tag {
  max-width: 100%;
  min-width: 0;
}

.tag-ellipsis {
  display: inline-block;
  max-width: min(100%, 360px);
  vertical-align: bottom;
}

.detail-ellipsis {
  display: block;
  max-width: 100%;
}

.pagination-bar {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(97, 113, 91, 0.1);
}

.page-size-control {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(64, 60, 51, 0.72);
}

.page-size-select {
  width: 86px;
}

.detail-block {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-block p {
  margin: 0;
}

.detail-label {
  color: rgba(64, 60, 51, 0.62);
  font-size: 12px;
}

.action-block,
.selection-sidecar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid rgba(97, 113, 91, 0.1);
}

.link-row {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(97, 113, 91, 0.12);
  background: rgba(247, 244, 236, 0.82);
  text-align: left;
  cursor: pointer;
}

.link-row strong {
  color: rgba(30, 78, 73, 0.92);
  font-weight: 500;
  word-break: break-all;
}

.empty-inspector,
.empty-state {
  padding: 18px 0;
}

.range-select-modal {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.range-select-copy {
  margin: 0;
}

.range-select-foot {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  color: rgba(64, 60, 51, 0.72);
}

@media (max-width: 1320px) {
  .workspace-layout {
    grid-template-columns: minmax(240px, 280px) minmax(0, 1fr);
  }

  .inspector-sidebar {
    position: static;
    grid-column: 1 / -1;
  }
}

@media (max-width: 980px) {
  .workspace-layout,
  .overview-strip {
    grid-template-columns: 1fr;
  }

  .filters-sidebar {
    position: static;
  }

  .review-hero,
  .record-head,
  .card-title-row,
  .selection-toolbar {
    flex-direction: column;
  }
}

@media (max-width: 680px) {
  .record-row,
  .year-range-grid,
  .range-select-grid {
    grid-template-columns: 1fr;
  }
}
</style>
