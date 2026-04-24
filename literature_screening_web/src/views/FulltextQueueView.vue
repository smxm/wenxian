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
  enrichWorkbench as requestEnrichWorkbench,
  patchWorkbenchItem as requestPatchWorkbenchItem,
  patchWorkbenchItems as requestPatchWorkbenchItems,
  rebuildWorkbench as requestRebuildWorkbench
} from '@/api/client'
import { useProjectsStore } from '@/stores/projects'
import type {
  ProjectDetail,
  TaskSnapshot,
  WorkbenchAccessStatus,
  WorkbenchCandidateItem,
  WorkbenchFinalDecision,
  WorkbenchStage,
  WorkbenchSummary
} from '@/types/api'

type CandidateSort = 'stage' | 'updated' | 'relevance-desc'
type WorkflowFilter = 'all' | 'needs-retrieval' | 'report-included' | 'blocked'
type StageSummaryCountKey = keyof Pick<
  WorkbenchSummary,
  'needs_link' | 'needs_access' | 'report_included' | 'report_excluded' | 'unavailable' | 'deferred'
>

const route = useRoute()
const router = useRouter()
const message = useMessage()
const projectsStore = useProjectsStore()

const projectId = computed(() => String(route.params.projectId))
const project = computed(() => projectsStore.currentProject)
const workbench = computed(() => project.value?.workbench ?? null)

const searchKeyword = ref('')
const workflowFilter = ref<WorkflowFilter>('all')
const stageFilter = ref<'all' | WorkbenchStage>('all')
const languageFilter = ref<'all' | 'zh' | 'en' | 'unknown'>('all')
const screeningFilter = ref<'all' | 'include' | 'exclude' | 'uncertain' | 'none'>('all')
const roundFilter = ref<'all' | string>('all')
const linkFilter = ref<'all' | 'has-link' | 'missing-link'>('all')
const yearStart = ref<number | null>(null)
const yearEnd = ref<number | null>(null)
const groupByStage = ref(false)
const sortMode = ref<CandidateSort>('stage')
const currentPage = ref(1)
const selectedCandidateIds = ref<string[]>([])
const activeCandidateId = ref<string | null>(null)
const workbenchSubmitting = ref(false)
const rebuildingWorkbench = ref(false)
const enrichingWorkbench = ref(false)
const sourceDatasetIds = ref<string[]>([])
const showRangeSelectModal = ref(false)
const rangeSelectionStart = ref<number | null>(null)
const rangeSelectionEnd = ref<number | null>(null)
const pageSize = 10
const currentCalendarYear = dayjs().year()

const stageMeta: Record<WorkbenchStage, { label: string; tone?: 'success' | 'error' | 'warning' | 'default' }> = {
  'needs-screening': { label: '来源待确认', tone: 'warning' },
  'screened-out': { label: '来源已排除', tone: 'error' },
  'needs-link': { label: '待补链接', tone: 'warning' },
  'needs-access': { label: '待获取全文', tone: 'default' },
  'ready-for-decision': { label: '已获取全文', tone: 'success' },
  'report-included': { label: '已纳入报告', tone: 'success' },
  'report-excluded': { label: '最终排除', tone: 'error' },
  unavailable: { label: '无权限获取', tone: 'error' },
  deferred: { label: '暂缓', tone: 'warning' }
}

const stageSummaryOrder: Array<{ key: WorkbenchStage; label: string; countKey: StageSummaryCountKey }> = [
  { key: 'needs-link', label: '缺少链接', countKey: 'needs_link' },
  { key: 'needs-access', label: '待获取全文', countKey: 'needs_access' },
  { key: 'report-included', label: '已纳入报告', countKey: 'report_included' },
  { key: 'report-excluded', label: '最终排除', countKey: 'report_excluded' },
  { key: 'unavailable', label: '无权限', countKey: 'unavailable' },
  { key: 'deferred', label: '暂缓', countKey: 'deferred' }
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

const screeningTaskMap = computed(
  () => new Map((project.value?.tasks ?? []).filter((task) => task.kind === 'screening').map((task) => [task.id, task]))
)

const workbenchSummary = computed(() => workbench.value?.summary ?? {
  total_candidates: 0,
  actionable_candidates: 0,
  needs_screening: 0,
  screened_out: 0,
  needs_link: 0,
  needs_access: 0,
  ready_for_decision: 0,
  report_included: 0,
  report_excluded: 0,
  unavailable: 0,
  deferred: 0
})

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
const normalizedYearBounds = computed(() => {
  const start = yearStart.value
  const end = yearEnd.value
  if (start !== null && end !== null) {
    return { start: Math.min(start, end), end: Math.max(start, end) }
  }
  return { start, end }
})

const primaryWorkflowCards = computed(() => [
  {
    key: 'all' as WorkflowFilter,
    label: '全部候选',
    count: workbenchSummary.value.total_candidates,
    description: '总览'
  },
  {
    key: 'needs-retrieval' as WorkflowFilter,
    label: '待获取全文',
    count: workbenchSummary.value.needs_link + workbenchSummary.value.needs_access,
    description: '先拿全文'
  },
  {
    key: 'report-included' as WorkflowFilter,
    label: '已纳入报告',
    count: workbenchSummary.value.report_included,
    description: '报告源'
  },
  {
    key: 'blocked' as WorkflowFilter,
    label: '暂未纳入',
    count: workbenchSummary.value.report_excluded + workbenchSummary.value.unavailable + workbenchSummary.value.deferred,
    description: '无权限 / 暂缓 / 排除'
  }
])

const secondaryStageChips = computed(() =>
  stageSummaryOrder
    .filter((item) => Number(workbenchSummary.value[item.countKey]) > 0)
    .map((item) => ({
      key: item.key,
      label: item.label,
      count: Number(workbenchSummary.value[item.countKey])
    }))
)

const workbenchItems = computed(() => workbench.value?.items ?? [])
const candidateMap = computed(() => new Map(workbenchItems.value.map((item) => [item.candidate_id, item])))
const selectedCandidateIdSet = computed(() => new Set(selectedCandidateIds.value))
const selectedCandidates = computed(() =>
  selectedCandidateIds.value
    .map((candidateId) => candidateMap.value.get(candidateId))
    .filter((item): item is WorkbenchCandidateItem => Boolean(item))
)

const filteredCandidates = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return workbenchItems.value
    .filter((item) => {
      if (workflowFilter.value === 'needs-retrieval' && !['needs-link', 'needs-access'].includes(item.stage)) return false
      if (workflowFilter.value === 'report-included' && item.stage !== 'report-included') return false
      if (workflowFilter.value === 'blocked' && !['report-excluded', 'unavailable', 'deferred'].includes(item.stage)) return false
      if (stageFilter.value !== 'all' && item.stage !== stageFilter.value) return false
      if (languageFilter.value !== 'all' && item.language !== languageFilter.value) return false
      if (screeningFilter.value !== 'all') {
        if (screeningFilter.value === 'none' && item.latest_screening_decision) return false
        if (screeningFilter.value !== 'none' && item.latest_screening_decision !== screeningFilter.value) return false
      }
      if (roundFilter.value !== 'all' && !item.screening_history.some((history) => history.task_id === roundFilter.value)) return false
      if (linkFilter.value === 'has-link' && !item.preferred_open_url && !item.preferred_pdf_url) return false
      if (linkFilter.value === 'missing-link' && (item.preferred_open_url || item.preferred_pdf_url)) return false
      if (normalizedYearBounds.value.start !== null || normalizedYearBounds.value.end !== null) {
        if (item.year === null || item.year === undefined) return false
        if (normalizedYearBounds.value.start !== null && item.year < normalizedYearBounds.value.start) return false
        if (normalizedYearBounds.value.end !== null && item.year > normalizedYearBounds.value.end) return false
      }
      if (!keyword) return true
      const haystack = [
        item.title,
        item.journal,
        item.doi,
        item.latest_screening_reason,
        item.source_round_labels.join(' '),
        item.source_dataset_labels.join(' ')
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(keyword)
    })
    .slice()
    .sort((left, right) => {
      if (sortMode.value === 'relevance-desc') {
        const leftConfidence = normalizedConfidence(left.latest_screening_confidence)
        const rightConfidence = normalizedConfidence(right.latest_screening_confidence)
        if (leftConfidence !== rightConfidence) return rightConfidence - leftConfidence
        return dayjs(right.updated_at).valueOf() - dayjs(left.updated_at).valueOf()
      }
      if (sortMode.value === 'updated') return dayjs(right.updated_at).valueOf() - dayjs(left.updated_at).valueOf()
      const stageOrder: WorkbenchStage[] = [
        'needs-link',
        'needs-access',
        'report-included',
        'unavailable',
        'deferred',
        'report-excluded',
        'needs-screening',
        'screened-out'
      ]
      const leftIndex = stageOrder.indexOf(left.stage)
      const rightIndex = stageOrder.indexOf(right.stage)
      if (leftIndex !== rightIndex) return leftIndex - rightIndex
      return (right.year ?? -Infinity) - (left.year ?? -Infinity)
    })
})

const pageCount = computed(() => Math.max(1, Math.ceil(filteredCandidates.value.length / pageSize)))
const currentPageStartIndex = computed(() => (filteredCandidates.value.length ? (currentPage.value - 1) * pageSize + 1 : 0))
const currentPageEndIndex = computed(() => Math.min(currentPage.value * pageSize, filteredCandidates.value.length))
const currentPageCandidates = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize
  return filteredCandidates.value.slice(startIndex, startIndex + pageSize)
})
const currentPageRangeLabel = computed(() =>
  currentPageCandidates.value.length ? `${currentPageStartIndex.value}-${currentPageEndIndex.value}` : '0-0'
)
const multiSelectOptions = computed(() => [
  {
    label: `当前筛选全部（${filteredCandidates.value.length} 篇）`,
    key: 'all-filtered',
    disabled: !filteredCandidates.value.length
  },
  {
    label: `当前页全部（第 ${currentPageRangeLabel.value} 条，共 ${currentPageCandidates.value.length} 篇）`,
    key: 'current-page',
    disabled: !currentPageCandidates.value.length
  },
  {
    label: '选择区间…',
    key: 'range',
    disabled: !filteredCandidates.value.length
  }
])

const groupedCandidates = computed(() => {
  const groups = new Map<WorkbenchStage, WorkbenchCandidateItem[]>()
  for (const item of currentPageCandidates.value) {
    if (!groups.has(item.stage)) groups.set(item.stage, [])
    groups.get(item.stage)?.push(item)
  }
  return Array.from(groups.entries())
})

const selectedPreferredUrls = computed(() =>
  Array.from(
    new Set(
      selectedCandidates.value
        .map((item) => item.preferred_open_url || item.preferred_pdf_url || null)
        .filter((url): url is string => Boolean(url))
    )
  )
)

const selectedPdfUrls = computed(() =>
  Array.from(new Set(selectedCandidates.value.map((item) => item.preferred_pdf_url).filter((url): url is string => Boolean(url))))
)

const selectedDoiUrls = computed(() =>
  Array.from(
    new Set(
      selectedCandidates.value
        .map((item) => item.links.find((link) => link.kind === 'doi')?.url ?? null)
        .filter((url): url is string => Boolean(url))
    )
  )
)

const activeWorkflowLabel = computed(() => {
  if (stageFilter.value !== 'all') return stageLabel(stageFilter.value)
  return primaryWorkflowCards.value.find((card) => card.key === workflowFilter.value)?.label ?? '全部候选'
})

function stageLabel(stage: WorkbenchStage) {
  return stageMeta[stage].label
}

function stageTagType(stage: WorkbenchStage) {
  return stageMeta[stage].tone
}

function screeningDecisionLabel(decision?: string | null) {
  if (decision === 'include') return '纳入'
  if (decision === 'exclude') return '剔除'
  if (decision === 'uncertain') return '不确定'
  return '尚未匹配筛选记录'
}

function screeningDecisionType(decision?: string | null) {
  if (decision === 'include') return 'success'
  if (decision === 'exclude') return 'error'
  if (decision === 'uncertain') return 'warning'
  return undefined
}

function accessStatusLabel(status: WorkbenchAccessStatus) {
  switch (status) {
    case 'ready':
      return '已获取全文'
    case 'unavailable':
      return '无权限获取'
    case 'deferred':
      return '暂缓'
    default:
      return '待获取全文'
  }
}

function finalDecisionLabel(decision: WorkbenchFinalDecision) {
  switch (decision) {
    case 'include':
      return '纳入报告'
    case 'exclude':
      return '最终排除'
    case 'deferred':
      return '暂不决定'
    default:
      return '跟随全文状态'
  }
}

function setWorkflowFilter(nextFilter: WorkflowFilter) {
  workflowFilter.value = nextFilter
  stageFilter.value = 'all'
}

function stageParentWorkflow(stage: WorkbenchStage): WorkflowFilter {
  if (stage === 'needs-link' || stage === 'needs-access') return 'needs-retrieval'
  if (stage === 'report-included') return 'report-included'
  if (stage === 'report-excluded' || stage === 'unavailable' || stage === 'deferred') return 'blocked'
  return 'all'
}

function setStageDetailFilter(stage: WorkbenchStage) {
  workflowFilter.value = stageParentWorkflow(stage)
  stageFilter.value = stage
}

function confidenceLabel(value?: number | string | null) {
  if (value === null || value === undefined || value === '') return null
  if (typeof value === 'number') return `${Math.round(value * 100)}%`
  const parsed = Number(value)
  return Number.isFinite(parsed) ? `${Math.round(parsed * 100)}%` : value
}

function normalizedConfidence(value?: number | string | null) {
  if (value === null || value === undefined || value === '') return -1
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return -1
    return value <= 1 ? value : value / 100
  }
  const cleaned = String(value).trim().replace('%', '')
  const parsed = Number(cleaned)
  if (!Number.isFinite(parsed)) return -1
  return parsed <= 1 ? parsed : parsed / 100
}

function roundLabel(taskId?: string | null, roundIndex?: number | null) {
  const task = taskId ? screeningTaskMap.value.get(taskId) : undefined
  const baseLabel = roundIndex ? `第 ${roundIndex} 轮` : task?.title || '未关联轮次'
  return task ? `${baseLabel}${screeningRoundStatusSuffix(task)}` : baseLabel
}

function candidateRoundLabels(item: WorkbenchCandidateItem) {
  const labels = item.screening_history.length
    ? item.screening_history
        .slice()
        .sort((left, right) => (left.round_index ?? 0) - (right.round_index ?? 0))
        .map((history) => roundLabel(history.task_id, history.round_index))
    : item.source_round_labels
  const uniqueLabels = Array.from(new Set(labels.filter(Boolean)))
  return uniqueLabels.length ? uniqueLabels : ['未关联轮次']
}

function candidateSummary(item: WorkbenchCandidateItem) {
  if (item.access_status === 'ready' && item.final_decision !== 'exclude' && item.final_decision !== 'deferred') {
    return '全文已获取，已自动进入报告源。'
  }
  if (item.final_decision === 'exclude') {
    return item.final_note || '这篇文献已从报告源中移除。'
  }
  if (item.access_status === 'unavailable') {
    return item.access_note || '当前无法获取全文。'
  }
  if (item.access_status === 'deferred') {
    return item.access_note || '这篇文献暂缓处理。'
  }
  return item.latest_screening_reason || `${accessStatusLabel(item.access_status)}，${finalDecisionLabel(item.final_decision)}`
}

function extractErrorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } } | null)?.response?.data?.detail
  if (typeof detail === 'string' && detail) return detail
  const messageText = (error as { message?: unknown } | null)?.message
  if (typeof messageText === 'string' && messageText) return messageText
  return fallback
}

function initializeWorkbenchState() {
  sourceDatasetIds.value = [...(workbench.value?.source_dataset_ids ?? [])]
}

function initializeCandidateSelection() {
  const validIds = new Set(workbenchItems.value.map((item) => item.candidate_id))
  selectedCandidateIds.value = selectedCandidateIds.value.filter((candidateId) => validIds.has(candidateId))
  if (activeCandidateId.value && !validIds.has(activeCandidateId.value)) {
    activeCandidateId.value = null
  }
}

function applyRouteIntent() {
  const requestedWorkflow = typeof route.query.workflow === 'string' ? route.query.workflow : null
  if (requestedWorkflow && ['all', 'needs-retrieval', 'report-included', 'blocked'].includes(requestedWorkflow)) {
    workflowFilter.value = requestedWorkflow as WorkflowFilter
  } else {
    workflowFilter.value = 'all'
  }
  const requestedStage = typeof route.query.stage === 'string' ? route.query.stage : null
  if (requestedStage && requestedStage in stageMeta) {
    stageFilter.value = requestedStage as WorkbenchStage
    workflowFilter.value = stageParentWorkflow(requestedStage as WorkbenchStage)
  } else {
    stageFilter.value = 'all'
  }
  const requestedTaskId = typeof route.query.screeningTaskId === 'string' ? route.query.screeningTaskId : null
  const validTaskIds = new Set(screeningRounds.value.map((item) => item.id))
  if (requestedTaskId && validTaskIds.has(requestedTaskId)) {
    roundFilter.value = requestedTaskId
  } else if (!validTaskIds.has(roundFilter.value)) {
    roundFilter.value = 'all'
  }
}

async function replaceRouteState() {
  await router.replace({
    query: {
      ...route.query,
      workflow: workflowFilter.value === 'all' ? undefined : workflowFilter.value,
      stage: stageFilter.value === 'all' ? undefined : stageFilter.value,
      screeningTaskId: roundFilter.value === 'all' ? undefined : roundFilter.value
    }
  })
}

async function loadProject() {
  await projectsStore.loadProject(projectId.value)
  initializeWorkbenchState()
  applyRouteIntent()
  initializeCandidateSelection()
}

watch(
  projectId,
  async () => {
    searchKeyword.value = ''
    selectedCandidateIds.value = []
    activeCandidateId.value = null
    await loadProject()
  },
  { immediate: true }
)

watch(
  () => [route.query.workflow, route.query.stage, route.query.screeningTaskId],
  async () => {
    if (!project.value) return
    applyRouteIntent()
  }
)

watch(workbench, () => {
  initializeWorkbenchState()
  initializeCandidateSelection()
})

watch(
  [searchKeyword, workflowFilter, stageFilter, languageFilter, screeningFilter, roundFilter, linkFilter, yearStart, yearEnd],
  () => {
    currentPage.value = 1
  }
)

watch(
  () => filteredCandidates.value.length,
  () => {
    if (currentPage.value > pageCount.value) currentPage.value = pageCount.value
    if (!filteredCandidates.value.length) currentPage.value = 1
  }
)

watch(
  [workflowFilter, stageFilter, roundFilter],
  async () => {
    if (!project.value) return
    await replaceRouteState()
  }
)

function setActiveCandidate(candidateId: string) {
  activeCandidateId.value = activeCandidateId.value === candidateId && selectedCandidateIds.value.length <= 1 ? null : candidateId
}

function toggleCandidateSelected(candidateId: string, checked: boolean) {
  if (checked) {
    if (!selectedCandidateIdSet.value.has(candidateId)) {
      selectedCandidateIds.value = [...selectedCandidateIds.value, candidateId]
    }
    activeCandidateId.value = candidateId
    return
  }
  selectedCandidateIds.value = selectedCandidateIds.value.filter((item) => item !== candidateId)
  if (activeCandidateId.value === candidateId && selectedCandidateIds.value.length > 1) {
    activeCandidateId.value = selectedCandidateIds.value[0] ?? null
  }
}

function shouldShowInlineActions(item: WorkbenchCandidateItem) {
  return activeCandidateId.value === item.candidate_id && selectedCandidateIds.value.length <= 1
}

function selectCandidateBatch(candidateIds: string[]) {
  const uniqueIds = Array.from(new Set(candidateIds.filter(Boolean)))
  if (!uniqueIds.length) return
  selectedCandidateIds.value = Array.from(new Set([...selectedCandidateIds.value, ...uniqueIds]))
  if (!activeCandidateId.value || !selectedCandidateIdSet.value.has(activeCandidateId.value)) {
    activeCandidateId.value = uniqueIds[0] ?? null
  }
}

function selectAllFilteredCandidates() {
  if (!filteredCandidates.value.length) return
  selectCandidateBatch(filteredCandidates.value.map((item) => item.candidate_id))
  message.success(`已选中当前筛选结果的 ${filteredCandidates.value.length} 篇文献`)
}

function selectCurrentPageCandidates() {
  if (!currentPageCandidates.value.length) return
  selectCandidateBatch(currentPageCandidates.value.map((item) => item.candidate_id))
  message.success(`已选中当前页的 ${currentPageCandidates.value.length} 篇文献`)
}

function openRangeSelectModal() {
  if (!filteredCandidates.value.length) return
  rangeSelectionStart.value = currentPageStartIndex.value || 1
  rangeSelectionEnd.value = currentPageEndIndex.value || Math.min(pageSize, filteredCandidates.value.length)
  showRangeSelectModal.value = true
}

function handleMultiSelectAction(key: string | number) {
  if (key === 'all-filtered') {
    selectAllFilteredCandidates()
    return
  }
  if (key === 'current-page') {
    selectCurrentPageCandidates()
    return
  }
  if (key === 'range') {
    openRangeSelectModal()
  }
}

function applyRangeSelection() {
  if (!filteredCandidates.value.length) return
  if (rangeSelectionStart.value === null || rangeSelectionEnd.value === null) {
    message.warning('请先填写起始条目和结束条目。')
    return
  }
  const normalizedStart = Math.max(1, Math.min(rangeSelectionStart.value, rangeSelectionEnd.value))
  const normalizedEnd = Math.min(filteredCandidates.value.length, Math.max(rangeSelectionStart.value, rangeSelectionEnd.value))
  const candidateIds = filteredCandidates.value
    .slice(normalizedStart - 1, normalizedEnd)
    .map((item) => item.candidate_id)
  if (!candidateIds.length) {
    message.warning('这个区间里没有可选文献。')
    return
  }
  selectCandidateBatch(candidateIds)
  showRangeSelectModal.value = false
  message.success(`已选中第 ${normalizedStart}-${normalizedEnd} 条，共 ${candidateIds.length} 篇文献`)
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

function clearPoolFilters() {
  searchKeyword.value = ''
  workflowFilter.value = 'all'
  stageFilter.value = 'all'
  roundFilter.value = 'all'
  languageFilter.value = 'all'
  screeningFilter.value = 'all'
  linkFilter.value = 'all'
  yearStart.value = null
  yearEnd.value = null
  groupByStage.value = false
  sortMode.value = 'stage'
  currentPage.value = 1
}

async function commitWorkbenchProject(nextProject: ProjectDetail) {
  projectsStore.currentProject = nextProject
  await projectsStore.refreshProjects()
  initializeWorkbenchState()
  applyRouteIntent()
  initializeCandidateSelection()
}

async function rebuildProjectWorkbench() {
  if (!project.value) return
  rebuildingWorkbench.value = true
  try {
    const updatedProject = await requestRebuildWorkbench(project.value.id, { source_dataset_ids: [...sourceDatasetIds.value] })
    await commitWorkbenchProject(updatedProject)
    message.success('候选文献工作台已按当前来源重建')
  } catch (error) {
    message.error(extractErrorMessage(error, '候选池重建失败'))
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

async function patchCandidate(candidateId: string, payload: {
  access_status?: WorkbenchAccessStatus | null
  final_decision?: WorkbenchFinalDecision | null
  access_note?: string | null
  final_note?: string | null
  preferred_open_url?: string | null
  preferred_pdf_url?: string | null
}) {
  if (!project.value) return
  workbenchSubmitting.value = true
  try {
    activeCandidateId.value = candidateId
    const updatedProject = await requestPatchWorkbenchItem(project.value.id, candidateId, payload)
    await commitWorkbenchProject(updatedProject)
    message.success('工作台记录已保存')
  } catch (error) {
    message.error(extractErrorMessage(error, '候选文献保存失败'))
  } finally {
    workbenchSubmitting.value = false
  }
}

async function patchSelectedCandidates(payload: {
  access_status?: WorkbenchAccessStatus | null
  final_decision?: WorkbenchFinalDecision | null
  access_note?: string | null
  final_note?: string | null
}) {
  if (!project.value || !selectedCandidateIds.value.length) return
  workbenchSubmitting.value = true
  try {
    const updatedProject = await requestPatchWorkbenchItems(project.value.id, {
      candidate_ids: [...selectedCandidateIds.value],
      ...payload
    })
    await commitWorkbenchProject(updatedProject)
    message.success('批量工作台操作已保存')
    selectedCandidateIds.value = []
  } catch (error) {
    message.error(extractErrorMessage(error, '批量操作失败'))
  } finally {
    workbenchSubmitting.value = false
  }
}

async function setCandidateAccessStatus(item: WorkbenchCandidateItem, status: WorkbenchAccessStatus) {
  await patchCandidate(item.candidate_id, {
    access_status: status,
    access_note: item.access_note ?? ''
  })
}

async function setCandidateFinalDecision(item: WorkbenchCandidateItem, decision: WorkbenchFinalDecision) {
  if (decision === 'include' && item.access_status !== 'ready') {
    message.warning('只有已经拿到全文的文献，才能恢复到报告源。')
    return
  }
  await patchCandidate(item.candidate_id, {
    final_decision: decision,
    final_note: item.final_note ?? ''
  })
}
</script>

<template>
  <div class="review-page">
    <NSpin :show="projectsStore.loadingDetail && !project">
      <div v-if="project" class="review-stack">
        <section class="review-hero">
          <div class="hero-main">
            <div class="eyebrow">Fulltext Workspace</div>
            <h1>全文获取工作台</h1>
            <p>打开链接、拿到全文、标记状态；拿到全文的文献会自动进入报告源。</p>
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
          <NCard class="panel-surface overview-card focus-board" embedded>
            <div class="card-title-row">
              <div>
                <div class="section-title">候选处理概览</div>
                <div class="section-copy">按全文获取进度和报告去留查看当前候选池。</div>
              </div>
              <div class="section-meta">候选 {{ workbenchSummary.total_candidates }} 篇</div>
            </div>
            <div class="workflow-cards">
              <button
                v-for="card in primaryWorkflowCards"
                :key="card.key"
                class="workflow-card"
                :class="{ active: workflowFilter === card.key }"
                type="button"
                @click="setWorkflowFilter(card.key)"
              >
                <span class="workflow-label">{{ card.label }}</span>
                <strong>{{ card.count }}</strong>
                <small>{{ card.description }}</small>
              </button>
            </div>
            <div v-if="secondaryStageChips.length" class="detail-chip-row">
              <button
                v-for="chip in secondaryStageChips"
                :key="chip.key"
                class="detail-chip"
                :class="{ active: stageFilter === chip.key }"
                type="button"
                @click="setStageDetailFilter(chip.key)"
              >
                {{ chip.label }} {{ chip.count }}
              </button>
            </div>
          </NCard>
        </section>

        <section class="workspace-layout">
          <aside class="filters-sidebar">
            <NCard class="panel-surface filter-panel" embedded>
              <div class="card-title-row sidebar-title-row">
                <div>
                  <div class="section-title">筛选与来源</div>
                  <div class="section-copy">像检索平台一样先收窄结果，再逐篇处理。</div>
                </div>
                <div class="section-meta">{{ filteredCandidates.length }} 篇</div>
              </div>

              <div class="filter-panel-stack">
                <div class="filter-section">
                  <div class="filter-section-title">关键词</div>
                  <NInput v-model:value="searchKeyword" placeholder="搜标题、期刊、DOI 或轮次来源">
                    <template #prefix><Search :size="16" /></template>
                  </NInput>
                </div>

                <div class="filter-section">
                  <div class="filter-section-title">轮次与排序</div>
                  <div class="filter-control-grid">
                    <NSelect v-model:value="roundFilter" :options="roundFilterOptions" />
                    <NSelect
                      v-model:value="sortMode"
                      :options="[
                        { label: '默认排序（按阶段）', value: 'stage' },
                        { label: '按相关度从高到低', value: 'relevance-desc' },
                        { label: '按最近更新', value: 'updated' }
                      ]"
                    />
                  </div>
                </div>

                <div class="filter-section">
                  <div class="filter-section-title">结果筛选</div>
                  <div class="filter-control-grid">
                    <NSelect
                      v-model:value="languageFilter"
                      :options="[
                        { label: '全部语言', value: 'all' },
                        { label: '中文', value: 'zh' },
                        { label: '英文', value: 'en' },
                        { label: '未知', value: 'unknown' }
                      ]"
                    />
                    <NSelect
                      v-model:value="screeningFilter"
                      :options="[
                        { label: '全部筛选结论', value: 'all' },
                        { label: '纳入', value: 'include' },
                        { label: '剔除', value: 'exclude' },
                        { label: '不确定', value: 'uncertain' },
                        { label: '未匹配轮次', value: 'none' }
                      ]"
                    />
                    <NSelect
                      v-model:value="linkFilter"
                      :options="[
                        { label: '全部链接状态', value: 'all' },
                        { label: '有可打开链接', value: 'has-link' },
                        { label: '缺少链接', value: 'missing-link' }
                      ]"
                    />
                    <div class="year-range-grid">
                      <NInputNumber v-model:value="yearStart" clearable :show-button="false" :min="1900" :max="currentCalendarYear" placeholder="起始年份" />
                      <NInputNumber v-model:value="yearEnd" clearable :show-button="false" :min="1900" :max="currentCalendarYear" placeholder="结束年份" />
                    </div>
                  </div>
                </div>

                <div class="filter-section">
                  <div class="filter-section-title">来源与同步</div>
                  <NForm label-placement="top">
                    <NFormItem label="候选来源数据集">
                      <NSelect v-model:value="sourceDatasetIds" multiple :options="workbenchSourceOptions" />
                    </NFormItem>
                  </NForm>
                  <div class="toolbar-actions">
                    <NButton type="primary" :loading="rebuildingWorkbench" :disabled="!sourceDatasetIds.length || enrichingWorkbench" @click="rebuildProjectWorkbench">
                      重建候选池
                    </NButton>
                    <NButton secondary :loading="enrichingWorkbench" :disabled="rebuildingWorkbench" @click="enrichProjectWorkbench">
                      <template #icon><RefreshCw :size="16" /></template>
                      刷新 OA / PDF
                    </NButton>
                  </div>
                </div>

                <div class="filter-actions filter-sidebar-actions">
                  <NButton tertiary @click="groupByStage = !groupByStage">
                    {{ groupByStage ? '切回普通列表' : '按阶段分组看' }}
                  </NButton>
                  <NDropdown trigger="click" :options="multiSelectOptions" @select="handleMultiSelectAction">
                    <NButton tertiary :disabled="!filteredCandidates.length || workbenchSubmitting">多选</NButton>
                  </NDropdown>
                  <NButton tertiary @click="clearPoolFilters">清空筛选</NButton>
                </div>
              </div>
            </NCard>
          </aside>

          <div class="workspace-main">
            <div class="results-column">
              <NCard class="panel-surface records-card" embedded>
              <div class="card-title-row">
                <div>
                  <div class="section-title">全文候选结果</div>
                  <div class="section-copy">根据左侧条件收窄结果，点开单篇后直接在文献卡片下完成全文获取和去留标记。</div>
                </div>
                <div class="section-meta">{{ activeWorkflowLabel }} · {{ filteredCandidates.length }} / {{ workbenchItems.length }} 篇</div>
              </div>

              <div class="results-toolbar">
                <div class="results-toolbar-copy">
                  当前显示第 {{ currentPageStartIndex || 0 }}-{{ currentPageEndIndex || 0 }} 条，共 {{ filteredCandidates.length }} 条
                </div>
              </div>

              <div v-if="selectedCandidateIds.length > 1" class="selection-toolbar">
                <div class="selection-summary">
                  <strong>已选 {{ selectedCandidateIds.length }} 篇</strong>
                  <span>批量动作只作用于已勾选文献；标记“已获取”后会自动进入报告源。</span>
                </div>
                <div class="selection-actions">
                  <NDropdown trigger="click" :options="multiSelectOptions" @select="handleMultiSelectAction">
                    <NButton secondary size="small" :disabled="!filteredCandidates.length || workbenchSubmitting">多选</NButton>
                  </NDropdown>
                  <NButton tertiary size="small" :disabled="!selectedPreferredUrls.length" @click="openMany(selectedPreferredUrls, '首选链接')">
                    打开首选链接
                  </NButton>
                  <NButton tertiary size="small" :disabled="!selectedPdfUrls.length" @click="openMany(selectedPdfUrls, 'PDF')">
                    打开 PDF
                  </NButton>
                  <NButton tertiary size="small" :disabled="!selectedDoiUrls.length" @click="openMany(selectedDoiUrls, 'DOI')">
                    打开 DOI
                  </NButton>
                  <NButton type="success" size="small" :disabled="!selectedCandidateIds.length || workbenchSubmitting" :loading="workbenchSubmitting" @click="patchSelectedCandidates({ access_status: 'ready' })">
                    标记已获取
                  </NButton>
                  <NButton type="error" size="small" :disabled="!selectedCandidateIds.length || workbenchSubmitting" :loading="workbenchSubmitting" @click="patchSelectedCandidates({ access_status: 'unavailable' })">
                    标记无权限
                  </NButton>
                  <NButton type="warning" size="small" :disabled="!selectedCandidateIds.length || workbenchSubmitting" :loading="workbenchSubmitting" @click="patchSelectedCandidates({ access_status: 'deferred' })">
                    暂缓
                  </NButton>
                  <NButton type="error" size="small" :disabled="!selectedCandidateIds.length || workbenchSubmitting" :loading="workbenchSubmitting" @click="patchSelectedCandidates({ final_decision: 'exclude' })">
                    移出报告
                  </NButton>
                  <NButton tertiary size="small" :disabled="!selectedCandidateIds.length || workbenchSubmitting" @click="selectedCandidateIds = []">
                    清空勾选
                  </NButton>
                </div>
              </div>

              <template v-if="groupByStage">
                    <div v-if="groupedCandidates.length" class="group-stack">
                      <section v-for="[stage, items] in groupedCandidates" :key="stage" class="stage-group">
                        <div class="stage-group-head">
                          <h3>{{ stageLabel(stage) }}</h3>
                          <span>{{ items.length }} 篇</span>
                        </div>
                        <article
                          v-for="item in items"
                          :key="item.candidate_id"
                          class="record-row"
                          :class="{ active: activeCandidateId === item.candidate_id }"
                          @click="setActiveCandidate(item.candidate_id)"
                        >
                          <div class="record-check">
                            <NCheckbox
                              :checked="selectedCandidateIdSet.has(item.candidate_id)"
                              @click.stop
                              @update:checked="(checked) => toggleCandidateSelected(item.candidate_id, checked)"
                            />
                          </div>
                          <div class="record-main">
                            <div class="record-head">
                                <div class="record-heading-block">
                                  <h2>{{ item.title }}</h2>
                                <div class="record-meta">{{ item.journal || '未知期刊' }} · {{ candidateRoundLabels(item).join('、') }}</div>
                              </div>
                              <div class="record-tags">
                                <NTag round size="small" :type="stageTagType(item.stage)">{{ stageLabel(item.stage) }}</NTag>
                                <NTag round size="small">{{ item.year ?? '----' }}</NTag>
                              </div>
                            </div>
                            <div class="record-reason">{{ candidateSummary(item) }}</div>
                            <div class="record-quick-actions">
                              <span class="record-stage-copy">{{ finalDecisionLabel(item.final_decision) }} · {{ accessStatusLabel(item.access_status) }}</span>
                              <span class="record-inline-hint">{{ shouldShowInlineActions(item) ? '收起单篇操作' : '点击卡片展开单篇操作' }}</span>
                            </div>
                            <div v-if="shouldShowInlineActions(item)" class="record-inline-panel" @click.stop>
                              <div class="record-inline-head">
                                <div class="record-inline-title">单篇操作</div>
                                <div class="record-inline-tags">
                                  <NTag round size="small" :type="screeningDecisionType(item.latest_screening_decision)">{{ screeningDecisionLabel(item.latest_screening_decision) }}</NTag>
                                  <NTag round size="small" :type="stageTagType(item.stage)">{{ stageLabel(item.stage) }}</NTag>
                                </div>
                              </div>
                              <div class="record-inline-actions">
                                <NButton secondary size="small" :disabled="!item.preferred_open_url && !item.preferred_pdf_url" @click.stop="openExternal(item.preferred_open_url || item.preferred_pdf_url)">
                                  打开链接
                                </NButton>
                                <NButton tertiary size="small" :disabled="!item.preferred_pdf_url" @click.stop="openExternal(item.preferred_pdf_url)">
                                  PDF
                                </NButton>
                                <NButton tertiary size="small" :disabled="!item.links.some((link) => link.kind === 'doi')" @click.stop="openExternal(item.links.find((link) => link.kind === 'doi')?.url ?? null)">
                                  DOI
                                </NButton>
                                <NButton type="success" size="small" :loading="workbenchSubmitting && activeCandidateId === item.candidate_id" @click.stop="setCandidateAccessStatus(item, 'ready')">
                                  标记已获取
                                </NButton>
                                <NButton type="error" size="small" :loading="workbenchSubmitting && activeCandidateId === item.candidate_id" @click.stop="setCandidateAccessStatus(item, 'unavailable')">
                                  标记无权限
                                </NButton>
                                <NButton type="warning" size="small" :loading="workbenchSubmitting && activeCandidateId === item.candidate_id" @click.stop="setCandidateAccessStatus(item, 'deferred')">
                                  暂缓
                                </NButton>
                                <NButton type="error" size="small" :loading="workbenchSubmitting && activeCandidateId === item.candidate_id" @click.stop="setCandidateFinalDecision(item, 'exclude')">
                                  移出报告
                                </NButton>
                                <NButton
                                  v-if="item.access_status === 'ready' && item.final_decision !== 'include'"
                                  type="success"
                                  size="small"
                                  tertiary
                                  :loading="workbenchSubmitting && activeCandidateId === item.candidate_id"
                                  @click.stop="setCandidateFinalDecision(item, 'include')"
                                >
                                  恢复纳入
                                </NButton>
                              </div>
                            </div>
                          </div>
                        </article>
                      </section>
                    </div>
                    <NEmpty v-else class="empty-state" description="当前筛选条件下没有匹配文献" />
                  </template>

                  <div v-else-if="currentPageCandidates.length" class="record-list">
                    <article
                      v-for="item in currentPageCandidates"
                      :key="item.candidate_id"
                      class="record-row"
                      :class="{ active: activeCandidateId === item.candidate_id }"
                      @click="setActiveCandidate(item.candidate_id)"
                    >
                      <div class="record-check">
                        <NCheckbox
                          :checked="selectedCandidateIdSet.has(item.candidate_id)"
                          @click.stop
                          @update:checked="(checked) => toggleCandidateSelected(item.candidate_id, checked)"
                        />
                      </div>
                      <div class="record-main">
                        <div class="record-head">
                          <div class="record-heading-block">
                            <h2>{{ item.title }}</h2>
                            <div class="record-meta">{{ item.journal || '未知期刊' }} · {{ candidateRoundLabels(item).join('、') }}</div>
                          </div>
                          <div class="record-tags">
                            <NTag round size="small" :type="screeningDecisionType(item.latest_screening_decision)">{{ screeningDecisionLabel(item.latest_screening_decision) }}</NTag>
                            <NTag round size="small" :type="stageTagType(item.stage)">{{ stageLabel(item.stage) }}</NTag>
                            <NTag round size="small">{{ item.year ?? '----' }}</NTag>
                            <NTag v-if="confidenceLabel(item.latest_screening_confidence)" round size="small" type="success">
                              相关度 {{ confidenceLabel(item.latest_screening_confidence) }}
                            </NTag>
                          </div>
                        </div>
                        <div class="record-reason">{{ candidateSummary(item) }}</div>
                        <div class="record-quick-actions">
                          <span class="record-stage-copy">{{ finalDecisionLabel(item.final_decision) }} · {{ accessStatusLabel(item.access_status) }}</span>
                          <span class="record-inline-hint">{{ shouldShowInlineActions(item) ? '收起单篇操作' : '点击卡片展开单篇操作' }}</span>
                        </div>
                        <div v-if="shouldShowInlineActions(item)" class="record-inline-panel" @click.stop>
                          <div class="record-inline-head">
                            <div class="record-inline-title">单篇操作</div>
                            <div class="record-inline-tags">
                              <NTag round size="small" :type="screeningDecisionType(item.latest_screening_decision)">{{ screeningDecisionLabel(item.latest_screening_decision) }}</NTag>
                              <NTag round size="small" :type="stageTagType(item.stage)">{{ stageLabel(item.stage) }}</NTag>
                            </div>
                          </div>
                          <div class="record-inline-actions">
                            <NButton secondary size="small" :disabled="!item.preferred_open_url && !item.preferred_pdf_url" @click.stop="openExternal(item.preferred_open_url || item.preferred_pdf_url)">
                              打开链接
                            </NButton>
                            <NButton tertiary size="small" :disabled="!item.preferred_pdf_url" @click.stop="openExternal(item.preferred_pdf_url)">
                              PDF
                            </NButton>
                            <NButton tertiary size="small" :disabled="!item.links.some((link) => link.kind === 'doi')" @click.stop="openExternal(item.links.find((link) => link.kind === 'doi')?.url ?? null)">
                              DOI
                            </NButton>
                            <NButton type="success" size="small" :loading="workbenchSubmitting && activeCandidateId === item.candidate_id" @click.stop="setCandidateAccessStatus(item, 'ready')">
                              标记已获取
                            </NButton>
                            <NButton type="error" size="small" :loading="workbenchSubmitting && activeCandidateId === item.candidate_id" @click.stop="setCandidateAccessStatus(item, 'unavailable')">
                              标记无权限
                            </NButton>
                            <NButton type="warning" size="small" :loading="workbenchSubmitting && activeCandidateId === item.candidate_id" @click.stop="setCandidateAccessStatus(item, 'deferred')">
                              暂缓
                            </NButton>
                            <NButton type="error" size="small" :loading="workbenchSubmitting && activeCandidateId === item.candidate_id" @click.stop="setCandidateFinalDecision(item, 'exclude')">
                              移出报告
                            </NButton>
                            <NButton
                              v-if="item.access_status === 'ready' && item.final_decision !== 'include'"
                              type="success"
                              size="small"
                              tertiary
                              :loading="workbenchSubmitting && activeCandidateId === item.candidate_id"
                              @click.stop="setCandidateFinalDecision(item, 'include')"
                            >
                              恢复纳入
                            </NButton>
                          </div>
                        </div>
                      </div>
                    </article>
                  </div>

              <NEmpty v-else class="empty-state" description="当前筛选条件下没有匹配文献" />
              </NCard>

              <div v-if="filteredCandidates.length > pageSize" class="pagination-bar">
                <div class="pagination-copy">每页 10 篇 · 当前页 {{ currentPage }} / {{ pageCount }}</div>
                <NPagination v-model:page="currentPage" :page-count="pageCount" />
              </div>
            </div>
          </div>
        </section>
      </div>

      <NEmpty v-else class="panel-surface empty-state" description="主题不存在或仍在加载中" />
    </NSpin>

    <NModal v-model:show="showRangeSelectModal" preset="card" title="按区间多选" style="width: 420px" :bordered="false">
      <div class="range-select-modal">
        <p class="range-select-copy">按当前筛选结果的顺序选择条目，例如 1-10、21-30。</p>
        <div class="range-select-grid">
          <NFormItem label="起始条目">
            <NInputNumber v-model:value="rangeSelectionStart" :show-button="false" :min="1" :max="filteredCandidates.length || 1" placeholder="例如 1" />
          </NFormItem>
          <NFormItem label="结束条目">
            <NInputNumber v-model:value="rangeSelectionEnd" :show-button="false" :min="1" :max="filteredCandidates.length || 1" placeholder="例如 10" />
          </NFormItem>
        </div>
        <div class="range-select-foot">
          <span>当前可选范围：1-{{ filteredCandidates.length }}</span>
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
.review-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.review-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.review-hero,
.overview-card,
.records-card,
.inspector-card {
  border-radius: 22px;
}

.review-hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 26px 28px;
  background:
    radial-gradient(circle at top left, rgba(255, 208, 130, 0.35), transparent 35%),
    linear-gradient(135deg, rgba(241, 244, 232, 0.96), rgba(255, 252, 245, 0.96));
  border: 1px solid rgba(129, 120, 92, 0.12);
}

.hero-main h1 {
  margin: 6px 0 10px;
  font-size: 34px;
  line-height: 1.1;
}

.hero-main p {
  margin: 0;
  max-width: 760px;
  color: rgba(56, 53, 44, 0.8);
  line-height: 1.7;
}

.eyebrow {
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(120, 98, 46, 0.7);
}

.hero-actions {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.overview-strip {
  display: flex;
}

.workspace-layout {
  display: grid;
  grid-template-columns: minmax(280px, 320px) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.filters-sidebar {
  position: sticky;
  top: 24px;
  align-self: start;
}

.workspace-main,
.results-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.workspace-main {
  min-width: 0;
}

.filter-panel {
  background: rgba(255, 252, 246, 0.92);
  border: 1px solid rgba(129, 120, 92, 0.1);
}

.sidebar-title-row {
  margin-bottom: 18px;
}

.filter-panel-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-section + .filter-section {
  padding-top: 18px;
  border-top: 1px solid rgba(129, 120, 92, 0.1);
}

.filter-section-title {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(72, 68, 58, 0.72);
}

.filter-control-grid {
  display: grid;
  gap: 12px;
}

.filter-control-grid :deep(.n-base-selection),
.filter-control-grid :deep(.n-base-selection-label),
.filter-control-grid :deep(.n-base-selection-label__render-label) {
  min-width: 0;
}

.filter-control-grid :deep(.n-base-selection-label__render-label) {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.year-range-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.filter-sidebar-actions {
  margin-bottom: 0;
}

.card-title-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.card-title-row > *,
.record-main,
.record-head,
.record-heading-block,
.selection-summary,
.results-toolbar-copy,
.section-copy,
.section-meta {
  min-width: 0;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
}

.section-copy {
  line-height: 1.65;
}

.section-copy,
.detail-copy,
.hint-line,
.record-reason,
.record-meta,
.record-stage-copy,
.summary-line span,
.focus-meta,
.abstract-label,
.detail-label,
.link-row span {
  color: rgba(64, 60, 51, 0.75);
}

.section-meta {
  color: rgba(64, 60, 51, 0.68);
  text-align: right;
  overflow-wrap: anywhere;
}

.focus-board {
  background:
    linear-gradient(180deg, rgba(255, 252, 245, 0.92), rgba(248, 244, 233, 0.92));
  border: 1px solid rgba(129, 120, 92, 0.1);
}

.workflow-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.workflow-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
  padding: 16px 18px;
  border: 1px solid rgba(125, 117, 98, 0.14);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.82);
  color: #2e2a22;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.workflow-card:hover,
.workflow-card.active {
  transform: translateY(-1px);
  border-color: rgba(46, 94, 68, 0.28);
  box-shadow: 0 14px 26px rgba(44, 59, 47, 0.08);
}

.workflow-card.active {
  background: linear-gradient(180deg, rgba(23, 45, 19, 0.95), rgba(32, 59, 27, 0.95));
  color: #fff;
}

.workflow-card strong {
  font-size: 30px;
  line-height: 1;
}

.workflow-card small {
  font-size: 13px;
  line-height: 1.55;
  color: inherit;
  opacity: 0.8;
}

.workflow-label {
  font-size: 14px;
  letter-spacing: 0.02em;
}

.detail-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.detail-chip {
  border: 1px solid rgba(125, 117, 98, 0.16);
  background: rgba(255, 255, 255, 0.78);
  border-radius: 999px;
  padding: 9px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.detail-chip.active {
  background: rgba(23, 45, 19, 0.08);
  border-color: rgba(23, 45, 19, 0.25);
}

.summary-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.summary-box {
  min-width: 96px;
  padding: 10px 12px;
  border-radius: 18px;
  background: rgba(248, 245, 237, 0.95);
}

.summary-box span {
  display: block;
  color: rgba(64, 60, 51, 0.66);
  font-size: 12px;
}

.summary-box strong {
  font-size: 22px;
}

.toolbar-actions,
.action-grid,
.link-actions,
.filter-actions,
.selection-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.results-toolbar,
.pagination-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.results-toolbar {
  padding: 12px 14px;
  margin-bottom: 14px;
  border-radius: 18px;
  background: rgba(248, 245, 237, 0.92);
}

.results-toolbar-copy,
.pagination-copy {
  color: rgba(64, 60, 51, 0.72);
  line-height: 1.6;
}

.filter-actions {
  margin-bottom: 14px;
}

.selection-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 14px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(235, 243, 231, 0.98), rgba(247, 251, 245, 0.96));
  border: 1px solid rgba(111, 145, 111, 0.16);
}

.selection-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.selection-summary strong {
  font-size: 16px;
}

.record-list,
.group-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stage-group-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.record-row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 12px;
  padding: 16px;
  border-radius: 20px;
  border: 1px solid rgba(125, 117, 98, 0.14);
  background: rgba(255, 255, 255, 0.92);
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.record-row:hover,
.record-row.active {
  border-color: rgba(46, 94, 68, 0.34);
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(31, 45, 35, 0.08);
}

.record-check {
  padding-top: 4px;
}

.record-main {
  min-width: 0;
}

.record-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.record-head h2,
.record-focus-title {
  margin: 0;
  font-size: 18px;
  line-height: 1.3;
}

.record-heading-block {
  min-width: 0;
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

.record-quick-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.record-inline-hint {
  color: rgba(64, 60, 51, 0.62);
  font-size: 13px;
}

.record-inline-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(241, 247, 238, 0.96), rgba(251, 252, 248, 0.96));
  border: 1px solid rgba(111, 145, 111, 0.18);
}

.record-inline-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.record-inline-title {
  font-size: 14px;
  font-weight: 700;
  color: #304132;
}

.record-inline-tags,
.record-inline-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.record-reason {
  margin-top: 8px;
  line-height: 1.55;
}

.detail-grid,
.history-stack,
.link-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.compact-detail-grid {
  margin-top: 14px;
}

.detail-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-value {
  display: flex;
  gap: 10px;
  align-items: center;
}

.link-row,
.history-row {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(247, 244, 236, 0.88);
}

.selection-preview {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}

.preview-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(247, 244, 236, 0.88);
}

.history-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.abstract-block {
  margin: 16px 0;
}

.abstract-panel {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(247, 244, 236, 0.88);
  white-space: pre-wrap;
}

.mode-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(23, 45, 19, 0.08);
  color: #2e4a29;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mode-title {
  font-size: 18px;
  font-weight: 700;
}

.step-card {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 14px;
  padding: 16px;
  margin-top: 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(125, 117, 98, 0.12);
}

.step-index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: #172d13;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
}

.step-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.step-title {
  font-size: 17px;
  font-weight: 700;
}

.step-copy {
  margin-top: 4px;
  color: rgba(64, 60, 51, 0.75);
  line-height: 1.6;
}

.fold-panel {
  margin-top: 4px;
  border-radius: 16px;
  background: rgba(247, 244, 236, 0.88);
}

.fold-panel summary {
  cursor: pointer;
  padding: 14px 16px;
  font-weight: 600;
  color: #2f3a2e;
}

.fold-body {
  padding: 0 16px 16px;
}

.plain-link {
  color: #214f4a;
  text-decoration: none;
  word-break: break-all;
}

.plain-link:hover {
  text-decoration: underline;
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
  color: rgba(64, 60, 51, 0.76);
  line-height: 1.65;
}

.range-select-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.range-select-foot {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  color: rgba(64, 60, 51, 0.72);
}

.range-select-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 1420px) {
  .workspace-layout {
    grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
  }
}

@media (max-width: 1100px) {
  .workspace-layout {
    grid-template-columns: 1fr;
  }

  .review-hero {
    flex-direction: column;
  }

  .filters-sidebar {
    position: static;
  }

  .workflow-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .card-title-row,
  .results-toolbar,
  .pagination-bar,
  .record-inline-head,
  .range-select-foot,
  .step-head,
  .record-head,
  .selection-toolbar {
    flex-direction: column;
  }

  .workflow-cards {
    grid-template-columns: 1fr;
  }

  .record-row,
  .step-card,
  .year-range-grid,
  .range-select-grid {
    grid-template-columns: 1fr;
  }

  .step-index {
    width: 36px;
    height: 36px;
    border-radius: 12px;
  }
}
</style>
