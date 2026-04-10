<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import dayjs from 'dayjs'
import { ArrowLeft, FileText, RefreshCw, Search } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NCheckbox,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSpin,
  NTag,
  useMessage
} from 'naive-ui'
import { applyBulkReviewOverride, applyReviewOverride, applySelectionReviewOverride, fetchTask } from '@/api/client'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import type { DatasetRecord, FulltextQueueItem, FulltextStatus, ScreeningRecordRow, TaskDetail, TaskSnapshot } from '@/types/api'

type WorkspaceLane = 'all' | 'needs-screening' | 'needs-fulltext' | 'ready' | 'stopped'
type WorkspaceSort = 'year-desc' | 'year-asc' | 'relevance' | 'updated'

type ReviewWorkspaceRow = {
  paper_id: string
  title: string
  year?: number | null
  journal?: string | null
  doi?: string | null
  abstract?: string | null
  confidence?: number | string | null
  screeningDecision: 'include' | 'exclude' | 'uncertain'
  screeningReason: string
  fulltextItem: FulltextQueueItem | null
  fulltextStatus: FulltextStatus | null
  fulltextNote: string
  doiUrl?: string | null
  landingUrl?: string | null
  pdfUrl?: string | null
  oaStatus?: string | null
  updatedAt: string
  lane: Exclude<WorkspaceLane, 'all'>
}

const route = useRoute()
const message = useMessage()
const projectsStore = useProjectsStore()
const tasksStore = useTasksStore()

const projectId = computed(() => String(route.params.projectId))
const project = computed(() => projectsStore.currentProject)

const selectedScreeningTaskId = ref<string | null>(null)
const screeningTaskDetail = ref<TaskDetail | null>(null)
const loadingScreeningTask = ref(false)
const screeningSubmitting = ref(false)

const activePaperId = ref<string | null>(null)
const selectedPaperIds = ref<string[]>([])
const activeDecision = ref<'include' | 'exclude' | 'uncertain'>('include')
const activeReason = ref('')
const activeFulltextNote = ref('')

const batchReviewDecision = ref<'include' | 'exclude' | 'uncertain'>('exclude')
const batchReviewReason = ref('人工复核：批量修正')
const bulkReviewText = ref('')

const searchKeyword = ref('')
const laneFilter = ref<WorkspaceLane>('all')
const sortMode = ref<WorkspaceSort>('year-desc')
const fulltextSourceDatasetIds = ref<string[]>([])

const updatingPaperId = ref<string | null>(null)
const updatingStatus = ref<FulltextStatus | null>(null)
const batchUpdatingStatus = ref<FulltextStatus | null>(null)
const rebuildingQueue = ref(false)
const enrichingQueue = ref(false)
const lastActionText = ref('')

const screeningRounds = computed(() =>
  [...(project.value?.tasks ?? [])]
    .filter((task) => task.kind === 'screening' && task.status === 'succeeded')
    .sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf())
)

const screeningRoundOrder = computed(() =>
  [...(project.value?.tasks ?? [])]
    .filter((task) => task.kind === 'screening')
    .sort((a, b) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf())
)

const datasetMap = computed(() => {
  const map = new Map<string, DatasetRecord>()
  for (const dataset of project.value?.datasets ?? []) {
    map.set(dataset.id, dataset)
  }
  return map
})

const screeningTaskOptions = computed(() =>
  screeningRounds.value.map((task) => {
    const roundIndex = screeningRoundOrder.value.findIndex((item) => item.id === task.id) + 1
    const summary = task.summary ?? {}
    return {
      label: `第 ${roundIndex} 轮 · 纳入 ${Number(summary.included_count ?? 0)} / 剔除 ${Number(summary.excluded_count ?? 0)} / 不确定 ${Number(summary.uncertain_count ?? 0)}`,
      value: task.id
    }
  })
)

const selectedScreeningTaskLabel = computed(
  () => screeningTaskOptions.value.find((item) => item.value === selectedScreeningTaskId.value)?.label ?? '未选择筛选轮次'
)

const selectedScreeningSummary = computed(() => {
  const summary = screeningTaskDetail.value?.summary ?? {}
  return {
    included: Number(summary.included_count ?? 0),
    excluded: Number(summary.excluded_count ?? 0),
    uncertain: Number(summary.uncertain_count ?? 0),
    processed: Number(summary.processed_count ?? 0)
  }
})

function latestMatchingDataset(task: TaskSnapshot, kinds: string[]) {
  const matches = task.output_dataset_ids
    .map((datasetId) => datasetMap.value.get(datasetId) ?? null)
    .filter((dataset): dataset is DatasetRecord => Boolean(dataset && kinds.includes(dataset.kind)))
  return matches.length ? matches[matches.length - 1] : null
}

const cumulativeIncludedDataset = computed(
  () => (project.value?.datasets ?? []).find((dataset) => dataset.kind === 'cumulative_included') ?? null
)
const fulltextReadyDataset = computed(
  () => (project.value?.datasets ?? []).find((dataset) => dataset.kind === 'fulltext_ready') ?? null
)

const fulltextSourceOptions = computed(() => {
  const options: Array<{ label: string; value: string }> = []
  const pushOnce = (dataset: DatasetRecord | null, label: string) => {
    if (!dataset) return
    if (options.some((item) => item.value === dataset.id)) return
    options.push({
      label: `${label} · ${dataset.record_count ?? '-'} 篇`,
      value: dataset.id
    })
  }
  pushOnce(cumulativeIncludedDataset.value, '项目累计纳入')
  for (const round of screeningRounds.value) {
    const includedDataset = latestMatchingDataset(round, ['included_reviewed', 'included'])
    const roundIndex = screeningRoundOrder.value.findIndex((item) => item.id === round.id) + 1
    pushOnce(includedDataset, `第 ${roundIndex} 轮纳入`)
  }
  return options
})

const fulltextCounts = computed(() => {
  const counts = { pending: 0, ready: 0, excluded: 0, unavailable: 0, deferred: 0 }
  for (const item of project.value?.fulltext_queue ?? []) counts[item.status] += 1
  return counts
})

function initializeFulltextState() {
  if (!project.value) return
  if ((project.value.fulltext_source_dataset_ids ?? []).length) {
    fulltextSourceDatasetIds.value = [...project.value.fulltext_source_dataset_ids]
  } else if (fulltextSourceOptions.value.length) {
    fulltextSourceDatasetIds.value = [fulltextSourceOptions.value[0].value]
  } else {
    fulltextSourceDatasetIds.value = []
  }
}

function confidenceNumber(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === '') return null
  if (typeof value === 'number') return value
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function screeningDecisionLabel(decision: 'include' | 'exclude' | 'uncertain') {
  switch (decision) {
    case 'include':
      return '纳入'
    case 'exclude':
      return '剔除'
    default:
      return '不确定'
  }
}

function screeningDecisionTagType(decision: 'include' | 'exclude' | 'uncertain') {
  switch (decision) {
    case 'include':
      return 'success'
    case 'exclude':
      return 'error'
    default:
      return 'warning'
  }
}

function statusLabel(status: FulltextStatus) {
  switch (status) {
    case 'ready':
      return '已获取全文'
    case 'excluded':
      return '最终排除'
    case 'unavailable':
      return '无权限获取'
    case 'deferred':
      return '暂缓'
    default:
      return '待处理全文'
  }
}

function statusTagType(status: FulltextStatus) {
  switch (status) {
    case 'ready':
      return 'success'
    case 'excluded':
      return 'error'
    case 'unavailable':
      return 'error'
    case 'deferred':
      return 'warning'
    default:
      return undefined
  }
}

function rowLane(decision: 'include' | 'exclude' | 'uncertain', status: FulltextStatus | null): Exclude<WorkspaceLane, 'all'> {
  if (decision === 'uncertain') return 'needs-screening'
  if (decision === 'exclude') return 'stopped'
  if (status === 'ready') return 'ready'
  if (status === 'excluded' || status === 'unavailable') return 'stopped'
  return 'needs-fulltext'
}

const fulltextQueueMap = computed(() => new Map((project.value?.fulltext_queue ?? []).map((item) => [item.paper_id, item])))

const mergedRows = computed<ReviewWorkspaceRow[]>(() =>
  (screeningTaskDetail.value?.records ?? []).map((record) => {
    const fulltextItem = fulltextQueueMap.value.get(record.paper_id) ?? null
    const screeningDecision = (record.decision as 'include' | 'exclude' | 'uncertain') ?? 'uncertain'
    const fulltextStatus = fulltextItem?.status ?? null
    return {
      paper_id: record.paper_id,
      title: record.title,
      year: record.year,
      journal: record.journal,
      doi: record.doi,
      abstract: record.abstract,
      confidence: record.confidence,
      screeningDecision,
      screeningReason: record.reason,
      fulltextItem,
      fulltextStatus,
      fulltextNote: fulltextItem?.note ?? '',
      doiUrl: fulltextItem?.doi_url ?? (record.doi ? `https://doi.org/${record.doi}` : null),
      landingUrl: fulltextItem?.landing_url ?? null,
      pdfUrl: fulltextItem?.pdf_url ?? null,
      oaStatus: fulltextItem?.oa_status ?? null,
      updatedAt: fulltextItem?.updated_at ?? screeningTaskDetail.value?.updated_at ?? new Date().toISOString(),
      lane: rowLane(screeningDecision, fulltextStatus)
    }
  })
)

const mergedRowMap = computed(() => new Map(mergedRows.value.map((row) => [row.paper_id, row])))

const workspaceCounts = computed(() => {
  const counts = { total: mergedRows.value.length, needsScreening: 0, needsFulltext: 0, ready: 0, stopped: 0 }
  for (const row of mergedRows.value) {
    if (row.lane === 'needs-screening') counts.needsScreening += 1
    if (row.lane === 'needs-fulltext') counts.needsFulltext += 1
    if (row.lane === 'ready') counts.ready += 1
    if (row.lane === 'stopped') counts.stopped += 1
  }
  return counts
})

function compareByRelevance(left: ReviewWorkspaceRow, right: ReviewWorkspaceRow) {
  const leftConfidence = confidenceNumber(left.confidence) ?? -1
  const rightConfidence = confidenceNumber(right.confidence) ?? -1
  if (rightConfidence !== leftConfidence) return rightConfidence - leftConfidence
  const leftYear = left.year ?? -Infinity
  const rightYear = right.year ?? -Infinity
  if (rightYear !== leftYear) return rightYear - leftYear
  return left.title.localeCompare(right.title)
}

function compareByStage(left: ReviewWorkspaceRow, right: ReviewWorkspaceRow) {
  const order = { 'needs-screening': 0, 'needs-fulltext': 1, ready: 2, stopped: 3 }
  if (order[left.lane] !== order[right.lane]) return order[left.lane] - order[right.lane]
  return compareByRelevance(left, right)
}

const filteredRows = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return mergedRows.value
    .filter((row) => {
      if (laneFilter.value !== 'all' && row.lane !== laneFilter.value) return false
      if (!keyword) return true
      const haystack = [row.title, row.journal, row.doi, row.year, row.screeningReason]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(keyword)
    })
    .slice()
    .sort((left, right) => {
      if (sortMode.value === 'relevance') return compareByRelevance(left, right)
      if (sortMode.value === 'updated') return dayjs(right.updatedAt).valueOf() - dayjs(left.updatedAt).valueOf()
      if (sortMode.value === 'year-asc') {
        const leftYear = left.year ?? Infinity
        const rightYear = right.year ?? Infinity
        if (leftYear !== rightYear) return leftYear - rightYear
        return compareByRelevance(left, right)
      }
      if (sortMode.value === 'year-desc') {
        const leftYear = left.year ?? -Infinity
        const rightYear = right.year ?? -Infinity
        if (rightYear !== leftYear) return rightYear - leftYear
        return compareByRelevance(left, right)
      }
      return compareByStage(left, right)
    })
})

const filteredRowPaperIds = computed(() => filteredRows.value.map((row) => row.paper_id))
const selectedPaperIdSet = computed(() => new Set(selectedPaperIds.value))
const allFilteredSelected = computed(
  () => filteredRowPaperIds.value.length > 0 && filteredRowPaperIds.value.every((paperId) => selectedPaperIdSet.value.has(paperId))
)

const selectedRows = computed(() =>
  selectedPaperIds.value.map((paperId) => mergedRowMap.value.get(paperId)).filter((row): row is ReviewWorkspaceRow => Boolean(row))
)

const selectedDoiUrls = computed(() =>
  Array.from(
    new Set(selectedRows.value.map((row) => row.doiUrl).filter((url): url is string => Boolean(url)))
  )
)

const selectedIncludedPaperIds = computed(() =>
  selectedRows.value.filter((row) => row.screeningDecision === 'include').map((row) => row.paper_id)
)

const selectedQueueEligiblePaperIds = computed(() =>
  selectedRows.value.filter((row) => row.screeningDecision === 'include' && row.fulltextItem).map((row) => row.paper_id)
)

const selectedIncludeMissingQueueCount = computed(
  () => selectedRows.value.filter((row) => row.screeningDecision === 'include' && !row.fulltextItem).length
)

const activeRow = computed(() => (activePaperId.value ? mergedRowMap.value.get(activePaperId.value) ?? null : null))

const sourceSelectionDirty = computed(() => {
  const current = [...fulltextSourceDatasetIds.value].sort()
  const server = [...(project.value?.fulltext_source_dataset_ids ?? [])].sort()
  if (current.length !== server.length) return true
  return current.some((item, index) => item !== server[index])
})

const readyReportRoute = computed(() => {
  if (!project.value || !fulltextReadyDataset.value || (fulltextReadyDataset.value.record_count ?? 0) <= 0) return null
  return {
    path: `/threads/${project.value.id}`,
    query: { reportDatasetId: fulltextReadyDataset.value.id }
  }
})

function sourceSummary() {
  return fulltextSourceDatasetIds.value
    .map((datasetId) => fulltextSourceOptions.value.find((item) => item.value === datasetId)?.label ?? '')
    .filter(Boolean)
    .join('、')
}

function extractErrorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } } | null)?.response?.data?.detail
  if (typeof detail === 'string' && detail) return detail
  const messageText = (error as { message?: unknown } | null)?.message
  if (typeof messageText === 'string' && messageText) return messageText
  return fallback
}

function initializeReviewSelection() {
  const validIds = new Set((screeningTaskDetail.value?.records ?? []).map((row) => row.paper_id))
  selectedPaperIds.value = selectedPaperIds.value.filter((paperId) => validIds.has(paperId))
  if (activePaperId.value && !validIds.has(activePaperId.value)) {
    activePaperId.value = null
  }
}

function applyRouteIntent() {
  const requestedTaskId = typeof route.query.screeningTaskId === 'string' ? route.query.screeningTaskId : null
  const validTaskIds = new Set(screeningTaskOptions.value.map((item) => item.value))
  if (requestedTaskId && validTaskIds.has(requestedTaskId)) {
    selectedScreeningTaskId.value = requestedTaskId
  } else if (!selectedScreeningTaskId.value || !validTaskIds.has(selectedScreeningTaskId.value)) {
    selectedScreeningTaskId.value = screeningTaskOptions.value[0]?.value ?? null
  }
  const requestedStatus = typeof route.query.status === 'string' ? route.query.status : null
  if (requestedStatus === 'ready') {
    laneFilter.value = 'ready'
  } else if (requestedStatus === 'excluded' || requestedStatus === 'unavailable') {
    laneFilter.value = 'stopped'
  } else if (requestedStatus === 'pending' || requestedStatus === 'deferred') {
    laneFilter.value = 'needs-fulltext'
  } else {
    laneFilter.value = 'all'
  }
}

async function loadScreeningTask(taskId: string | null) {
  if (!taskId) {
    screeningTaskDetail.value = null
    initializeReviewSelection()
    return
  }
  loadingScreeningTask.value = true
  try {
    screeningTaskDetail.value = await fetchTask(taskId)
    initializeReviewSelection()
  } catch (error) {
    message.error(extractErrorMessage(error, '筛选轮次加载失败'))
  } finally {
    loadingScreeningTask.value = false
  }
}

async function loadProject() {
  await projectsStore.loadProject(projectId.value)
  initializeFulltextState()
  applyRouteIntent()
  await loadScreeningTask(selectedScreeningTaskId.value)
}

watch(
  projectId,
  async () => {
    searchKeyword.value = ''
    laneFilter.value = 'all'
    sortMode.value = 'year-desc'
    selectedPaperIds.value = []
    activePaperId.value = null
    lastActionText.value = ''
    await loadProject()
  },
  { immediate: true }
)

watch(
  () => [route.query.screeningTaskId, route.query.status],
  async () => {
    if (!project.value) return
    applyRouteIntent()
    if (selectedScreeningTaskId.value && selectedScreeningTaskId.value !== screeningTaskDetail.value?.id) {
      await loadScreeningTask(selectedScreeningTaskId.value)
    }
  }
)

watch(project, () => {
  if (!project.value) return
  initializeFulltextState()
  initializeReviewSelection()
})

watch(selectedScreeningTaskId, async (taskId, previousTaskId) => {
  if (!taskId || taskId === previousTaskId) return
  await loadScreeningTask(taskId)
})

watch(activeRow, (row) => {
  if (!row) {
    activeDecision.value = 'include'
    activeReason.value = ''
    activeFulltextNote.value = ''
    return
  }
  activeDecision.value = row.screeningDecision
  activeReason.value = row.screeningReason || ''
  activeFulltextNote.value = row.fulltextNote || ''
})

function setActiveRow(paperId: string) {
  activePaperId.value = paperId
}

function setPaperSelected(paperId: string, checked: boolean) {
  if (checked) {
    if (!selectedPaperIdSet.value.has(paperId)) {
      selectedPaperIds.value = [...selectedPaperIds.value, paperId]
    }
    if (!activePaperId.value) activePaperId.value = paperId
    return
  }
  selectedPaperIds.value = selectedPaperIds.value.filter((item) => item !== paperId)
}

function toggleSelectAllFiltered() {
  if (!filteredRowPaperIds.value.length) return
  if (allFilteredSelected.value) {
    const visible = new Set(filteredRowPaperIds.value)
    selectedPaperIds.value = selectedPaperIds.value.filter((paperId) => !visible.has(paperId))
    return
  }
  selectedPaperIds.value = Array.from(new Set([...selectedPaperIds.value, ...filteredRowPaperIds.value]))
  if (!activePaperId.value) activePaperId.value = filteredRowPaperIds.value[0] ?? null
}

function clearSelectedRows() {
  selectedPaperIds.value = []
}

async function refreshWorkspaceAfterReview(taskDetail: TaskDetail) {
  screeningTaskDetail.value = taskDetail
  await Promise.all([projectsStore.loadProject(projectId.value), tasksStore.refreshList()])
  initializeFulltextState()
  initializeReviewSelection()
}

async function submitActiveReviewOverride() {
  if (!screeningTaskDetail.value || !activeRow.value) return
  screeningSubmitting.value = true
  try {
    const updated = await applyReviewOverride(screeningTaskDetail.value.id, {
      paper_id: activeRow.value.paper_id,
      decision: activeDecision.value,
      reason: activeReason.value
    })
    await refreshWorkspaceAfterReview(updated)
    message.success('当前文献的筛选判定已保存')
  } catch (error) {
    message.error(extractErrorMessage(error, '筛选复核保存失败'))
  } finally {
    screeningSubmitting.value = false
  }
}

async function markSelectedAsReady() {
  if (!screeningTaskDetail.value || !project.value || !selectedPaperIds.value.length) return
  batchUpdatingStatus.value = 'ready'
  const selectedIds = [...selectedPaperIds.value]
  try {
    const idsNeedingInclude = selectedRows.value
      .filter((row) => row.screeningDecision !== 'include')
      .map((row) => row.paper_id)

    if (idsNeedingInclude.length) {
      const updated = await applySelectionReviewOverride(screeningTaskDetail.value.id, {
        paper_ids: idsNeedingInclude,
        decision: 'include',
        reason: '人工复核：转入全文获取'
      })
      screeningTaskDetail.value = updated
      await Promise.all([projectsStore.loadProject(projectId.value), tasksStore.refreshList()])
      initializeFulltextState()
      initializeReviewSelection()
    }

    let queueIdSet = new Set((projectsStore.currentProject?.fulltext_queue ?? []).map((item) => item.paper_id))
    const missingIds = selectedIds.filter((paperId) => !queueIdSet.has(paperId))
    if (missingIds.length) {
      const sourceIds = fulltextSourceDatasetIds.value.length
        ? [...fulltextSourceDatasetIds.value]
        : [...(projectsStore.currentProject?.fulltext_source_dataset_ids ?? [])]
      if (sourceIds.length) {
        await projectsStore.rebuildFulltextQueue(projectId.value, sourceIds)
        initializeFulltextState()
        initializeReviewSelection()
        queueIdSet = new Set((projectsStore.currentProject?.fulltext_queue ?? []).map((item) => item.paper_id))
      }
    }

    const readyIds = selectedIds.filter((paperId) => queueIdSet.has(paperId))
    if (readyIds.length) {
      await projectsStore.updateFulltextStatuses(projectId.value, {
        paper_ids: readyIds,
        status: 'ready',
        note: null
      })
      initializeFulltextState()
      initializeReviewSelection()
    }

    if (!readyIds.length) {
      message.warning('已批量改为纳入，但这些文献当前没有进入全文队列；请先确认全文来源设置。')
      return
    }

    lastActionText.value = `已将 ${readyIds.length} 篇文献批量标记为“已获取全文”。`
    message.success(`已将 ${readyIds.length} 篇文献批量标记为“已获取全文”`)
    selectedPaperIds.value = []
  } catch (error) {
    message.error(extractErrorMessage(error, '批量标记已获取全文失败'))
  } finally {
    batchUpdatingStatus.value = null
  }
}

async function submitBulkReviewOverride() {
  if (!screeningTaskDetail.value || !bulkReviewText.value.trim()) return
  screeningSubmitting.value = true
  try {
    const updated = await applyBulkReviewOverride(screeningTaskDetail.value.id, {
      entries_text: bulkReviewText.value,
      decision: batchReviewDecision.value,
      reason: batchReviewReason.value
    })
    await refreshWorkspaceAfterReview(updated)
    bulkReviewText.value = ''
    message.success('按标题或参考文献列表的批量改判已应用')
  } catch (error) {
    message.error(extractErrorMessage(error, '标题批量复核失败'))
  } finally {
    screeningSubmitting.value = false
  }
}

async function rebuildThreadFulltextQueue() {
  if (!project.value) return
  rebuildingQueue.value = true
  try {
    await projectsStore.rebuildFulltextQueue(project.value.id, [...fulltextSourceDatasetIds.value])
    lastActionText.value = sourceSummary()
      ? `已按“${sourceSummary()}”同步全文队列。`
      : '全文队列已同步。'
    message.success('全文队列已同步')
  } catch (error) {
    message.error(extractErrorMessage(error, '全文队列更新失败'))
  } finally {
    rebuildingQueue.value = false
  }
}

async function enrichThreadFulltextQueue() {
  if (!project.value) return
  enrichingQueue.value = true
  try {
    await projectsStore.enrichFulltextQueue(project.value.id)
    lastActionText.value = '已刷新 DOI 落地页与 OA / PDF 链接。'
    message.success('已刷新 DOI 落地页和 OA / 链接')
  } catch (error) {
    message.error(extractErrorMessage(error, 'OA / 链接刷新失败'))
  } finally {
    enrichingQueue.value = false
  }
}

async function updateThreadFulltextStatus(row: ReviewWorkspaceRow, status: FulltextStatus, noteOverride?: string) {
  if (!project.value) return
  updatingPaperId.value = row.paper_id
  updatingStatus.value = status
  try {
    await projectsStore.updateFulltextStatus(project.value.id, {
      paper_id: row.paper_id,
      status,
      note: noteOverride ?? row.fulltextNote ?? ''
    })
    lastActionText.value = `已将《${row.title}》标记为“${statusLabel(status)}”。`
    message.success(`${statusLabel(status)} 已保存`)
  } catch (error) {
    message.error(extractErrorMessage(error, '全文状态保存失败'))
  } finally {
    updatingPaperId.value = null
    updatingStatus.value = null
  }
}

async function saveActiveFulltextNote() {
  if (!activeRow.value?.fulltextItem) return
  await updateThreadFulltextStatus(activeRow.value, activeRow.value.fulltextStatus ?? 'pending', activeFulltextNote.value)
}

async function excludeSelectedRows() {
  if (!project.value || !selectedPaperIds.value.length) return
  batchUpdatingStatus.value = 'excluded'
  const selectedIds = [...selectedIncludedPaperIds.value]
  try {
    if (!selectedIds.length) {
      message.warning('当前勾选里没有处于“初筛纳入”状态的文献，因此没有可做最终排除的对象。')
      return
    }

    let queueIdSet = new Set((projectsStore.currentProject?.fulltext_queue ?? []).map((item) => item.paper_id))
    const missingIds = selectedIds.filter((paperId) => !queueIdSet.has(paperId))
    if (missingIds.length) {
      const sourceIds = fulltextSourceDatasetIds.value.length
        ? [...fulltextSourceDatasetIds.value]
        : [...(projectsStore.currentProject?.fulltext_source_dataset_ids ?? [])]
      if (sourceIds.length) {
        await projectsStore.rebuildFulltextQueue(projectId.value, sourceIds)
        initializeFulltextState()
        initializeReviewSelection()
        queueIdSet = new Set((projectsStore.currentProject?.fulltext_queue ?? []).map((item) => item.paper_id))
      }
    }

    const queueIds = selectedIds.filter((paperId) => queueIdSet.has(paperId))
    if (!queueIds.length) {
      message.warning('这些文献还没有进入全文队列，暂时无法做最终排除；请先确认全文来源设置。')
      return
    }

    await projectsStore.updateFulltextStatuses(project.value.id, {
      paper_ids: queueIds,
      status: 'excluded',
      note: null
    })
    await Promise.all([projectsStore.loadProject(projectId.value), tasksStore.refreshList()])
    initializeFulltextState()
    initializeReviewSelection()
    lastActionText.value = `已将 ${queueIds.length} 篇文献标记为“最终排除”，不会回写初筛结果。`
    message.success(`已将 ${queueIds.length} 篇文献标记为“最终排除”`)
    selectedPaperIds.value = []
  } catch (error) {
    message.error(extractErrorMessage(error, '批量最终排除失败'))
  } finally {
    batchUpdatingStatus.value = null
  }
}

async function copyDoi(doi?: string | null) {
  if (!doi) return
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(doi)
  } else {
    const input = document.createElement('input')
    input.value = doi
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
  }
  message.success('DOI 已复制')
}

function openExternal(url?: string | null) {
  if (!url) return
  window.open(url, '_blank', 'noopener')
}

function openSelectedDoiLinks() {
  if (!selectedDoiUrls.value.length) return
  let blockedCount = 0
  for (const url of selectedDoiUrls.value) {
    const opened = window.open(url, '_blank', 'noopener')
    if (!opened) blockedCount += 1
  }
  if (blockedCount > 0) {
    message.warning(`已尝试打开 ${selectedDoiUrls.value.length} 个 DOI，其中 ${blockedCount} 个可能被浏览器拦截。`)
    return
  }
  message.success(`已打开 ${selectedDoiUrls.value.length} 个 DOI 链接`)
}
</script>

<template>
  <div class="review-page">
    <NSpin :show="projectsStore.loadingDetail && !project">
      <div v-if="project" class="review-stack">
        <section class="review-hero">
          <div class="hero-main">
            <div class="eyebrow">Unified Review Workspace</div>
            <h1>统一复核工作台</h1>
            <p>这里把“筛选改判”和“全文处理”收成一条连续流水线。左边始终是当前筛选轮次的候选文献流，右边根据你点中的文献或勾选的批量结果切换操作，不会再默认帮你选中第一篇。</p>
          </div>
          <div class="hero-actions">
            <RouterLink :to="`/threads/${project.id}`">
              <NButton secondary>
                <template #icon><ArrowLeft :size="16" /></template>
                返回主题页
              </NButton>
            </RouterLink>
            <RouterLink v-if="readyReportRoute" :to="readyReportRoute">
              <NButton type="primary">
                <template #icon><FileText :size="16" /></template>
                用已获取全文生成报告
              </NButton>
            </RouterLink>
          </div>
        </section>

        <section class="overview-grid">
          <NCard class="panel-surface overview-card" embedded>
            <div class="card-title-row">
              <div>
                <div class="section-title">当前复核轮次</div>
                <div class="section-copy">选择要处理的筛选轮次。进入页面后不会默认选中文献，点击左侧条目后右侧才会进入单篇模式。</div>
              </div>
              <div class="section-meta">{{ selectedScreeningTaskLabel }}</div>
            </div>
            <NForm label-placement="top">
              <NFormItem label="筛选轮次">
                <NSelect
                  v-model:value="selectedScreeningTaskId"
                  :options="screeningTaskOptions"
                  placeholder="选择需要复核的筛选轮次"
                />
              </NFormItem>
            </NForm>
            <div class="summary-strip">
              <div class="summary-box">
                <span>纳入</span>
                <strong>{{ selectedScreeningSummary.included }}</strong>
              </div>
              <div class="summary-box">
                <span>剔除</span>
                <strong>{{ selectedScreeningSummary.excluded }}</strong>
              </div>
              <div class="summary-box">
                <span>不确定</span>
                <strong>{{ selectedScreeningSummary.uncertain }}</strong>
              </div>
              <div class="summary-box">
                <span>已处理</span>
                <strong>{{ selectedScreeningSummary.processed }}</strong>
              </div>
            </div>
          </NCard>

          <NCard class="panel-surface overview-card" embedded>
            <div class="card-title-row">
              <div>
                <div class="section-title">阶段分布</div>
                <div class="section-copy">筛选轮次里的每篇文献会落在一个阶段里，帮助你一眼看出应该先修正筛选，还是继续处理全文。</div>
              </div>
            </div>
            <div class="summary-strip">
              <button class="summary-chip" :class="{ active: laneFilter === 'all' }" type="button" @click="laneFilter = 'all'">
                全部 {{ workspaceCounts.total }}
              </button>
              <button class="summary-chip warning" :class="{ active: laneFilter === 'needs-screening' }" type="button" @click="laneFilter = 'needs-screening'">
                待筛选复核 {{ workspaceCounts.needsScreening }}
              </button>
              <button class="summary-chip" :class="{ active: laneFilter === 'needs-fulltext' }" type="button" @click="laneFilter = 'needs-fulltext'">
                待全文处理 {{ workspaceCounts.needsFulltext }}
              </button>
              <button class="summary-chip success" :class="{ active: laneFilter === 'ready' }" type="button" @click="laneFilter = 'ready'">
                已获取全文 {{ workspaceCounts.ready }}
              </button>
              <button class="summary-chip error" :class="{ active: laneFilter === 'stopped' }" type="button" @click="laneFilter = 'stopped'">
                已终止 {{ workspaceCounts.stopped }}
              </button>
            </div>
          </NCard>

          <NCard class="panel-surface overview-card" embedded>
            <div class="card-title-row">
              <div>
                <div class="section-title">全文来源与同步</div>
                <div class="section-copy">这里只控制“纳入”文献如何进入全文队列。筛选里改成不纳入后，对应记录会自然退出全文处理流程。</div>
              </div>
              <div class="section-meta">{{ sourceSummary() || '尚未选择来源' }}</div>
            </div>
            <NForm label-placement="top">
              <NFormItem label="全文来源">
                <NSelect v-model:value="fulltextSourceDatasetIds" multiple :options="fulltextSourceOptions" />
              </NFormItem>
            </NForm>
            <div class="toolbar-actions">
              <NButton
                :type="sourceSelectionDirty ? 'primary' : 'default'"
                :loading="rebuildingQueue"
                :disabled="!fulltextSourceDatasetIds.length || enrichingQueue"
                @click="rebuildThreadFulltextQueue"
              >
                同步全文队列
              </NButton>
              <NButton secondary :loading="enrichingQueue" :disabled="rebuildingQueue" @click="enrichThreadFulltextQueue">
                <template #icon><RefreshCw :size="16" /></template>
                刷新 OA / 链接
              </NButton>
            </div>
            <div class="summary-line">
              <span>项目全文队列</span>
              <strong>待处理 {{ fulltextCounts.pending }} · 已获取 {{ fulltextCounts.ready }} · 暂缓 {{ fulltextCounts.deferred }}</strong>
            </div>
            <div v-if="sourceSelectionDirty" class="hint-line">来源已改动，点击“同步全文队列”后才会更新列表和报告可用全文。</div>
          </NCard>
        </section>

        <section class="workspace-grid">
          <NCard class="panel-surface records-card" embedded>
            <div class="card-title-row">
              <div>
                <div class="section-title">候选文献流</div>
                <div class="section-copy">不再分“筛选页”和“全文页”。同一条记录里会同时显示筛选判定和全文阶段，点哪篇就处理哪篇，勾多篇就切到批量模式；DOI、落地页和 PDF 入口也直接保留在每条记录下面。</div>
              </div>
              <div class="section-meta">当前显示 {{ filteredRows.length }} / {{ mergedRows.length }} 篇</div>
            </div>

            <div v-if="lastActionText" class="inline-alert">
              <NAlert type="success" :show-icon="false">{{ lastActionText }}</NAlert>
            </div>

            <div class="records-toolbar">
              <NInput v-model:value="searchKeyword" placeholder="按标题、期刊、DOI、年份或理由搜索">
                <template #prefix>
                  <Search :size="16" />
                </template>
              </NInput>
              <NSelect
                v-model:value="sortMode"
                :options="[
                  { label: '按年份从新到旧（年内按相关度）', value: 'year-desc' },
                  { label: '按年份从旧到新（年内按相关度）', value: 'year-asc' },
                  { label: '按相关度', value: 'relevance' },
                  { label: '按最近更新', value: 'updated' }
                ]"
              />
            </div>

            <div class="batch-toolbar">
              <NButton secondary :disabled="!filteredRows.length || batchUpdatingStatus !== null" @click="toggleSelectAllFiltered">
                {{ allFilteredSelected ? '取消全选当前结果' : '全选当前结果' }}
              </NButton>
              <NButton tertiary :disabled="!selectedPaperIds.length || batchUpdatingStatus !== null" @click="clearSelectedRows">
                清空勾选
              </NButton>
              <div class="batch-copy">右侧不会自动选中文献；只有你点中条目或勾选结果时才会进入操作模式。</div>
            </div>

            <NSpin :show="loadingScreeningTask">
              <div v-if="filteredRows.length" class="record-list">
                <article
                  v-for="row in filteredRows"
                  :key="row.paper_id"
                  class="record-row"
                  :class="{ active: activePaperId === row.paper_id }"
                  @click="setActiveRow(row.paper_id)"
                >
                  <div class="record-check">
                    <NCheckbox
                      :checked="selectedPaperIdSet.has(row.paper_id)"
                      @click.stop
                      @update:checked="(checked) => setPaperSelected(row.paper_id, checked)"
                    />
                  </div>
                  <div class="record-main">
                    <div class="record-head">
                      <h2>{{ row.title }}</h2>
                      <div class="record-tags">
                        <NTag round size="small" :type="screeningDecisionTagType(row.screeningDecision)">
                          {{ screeningDecisionLabel(row.screeningDecision) }}
                        </NTag>
                        <NTag
                          v-if="row.screeningDecision === 'include' && row.fulltextStatus"
                          round
                          size="small"
                          :type="statusTagType(row.fulltextStatus)"
                        >
                          {{ statusLabel(row.fulltextStatus) }}
                        </NTag>
                        <NTag v-else-if="row.screeningDecision === 'include'" round size="small">待同步全文</NTag>
                        <NTag v-if="confidenceNumber(row.confidence) !== null" round size="small" type="success">
                          相关度 {{ Math.round((confidenceNumber(row.confidence) ?? 0) * 100) }}%
                        </NTag>
                        <NTag round size="small">{{ row.year ?? '----' }}</NTag>
                      </div>
                    </div>
                    <div class="record-meta">{{ row.journal || '未知期刊' }}</div>
                    <div v-if="row.screeningReason" class="record-reason">{{ row.screeningReason }}</div>
                    <div v-if="row.abstract" class="record-abstract">{{ row.abstract }}</div>
                    <div class="record-quick-actions">
                      <span class="record-stage-copy">
                        全文获取：
                        {{
                          row.screeningDecision === 'include'
                            ? row.fulltextItem
                              ? statusLabel(row.fulltextStatus ?? 'pending')
                              : '待同步到全文队列'
                            : '当前不进入全文获取'
                        }}
                      </span>
                      <NButton
                        v-if="row.screeningDecision === 'include' && !row.fulltextItem"
                        size="small"
                        tertiary
                        @click.stop="rebuildThreadFulltextQueue"
                      >
                        加入全文队列
                      </NButton>
                      <NButton v-if="row.doiUrl" text size="small" @click.stop="openExternal(row.doiUrl)">打开 DOI</NButton>
                      <NButton v-if="row.doi" text size="small" @click.stop="copyDoi(row.doi)">复制 DOI</NButton>
                      <NButton v-if="row.landingUrl" text size="small" @click.stop="openExternal(row.landingUrl)">打开落地页</NButton>
                      <NButton v-if="row.pdfUrl" text size="small" @click.stop="openExternal(row.pdfUrl)">打开 PDF</NButton>
                    </div>
                  </div>
                </article>
              </div>
              <NEmpty
                v-else
                class="empty-state"
                :description="screeningTaskDetail ? '当前筛选条件下没有匹配文献' : '当前线程还没有可复核的筛选轮次'"
              />
            </NSpin>
          </NCard>

          <div class="inspector-stack">
            <NCard class="panel-surface inspector-card" embedded>
              <div class="card-title-row">
                <div>
                  <div class="section-title">复核与全文操作</div>
                  <div class="section-copy">右侧根据你当前的选择自动切换成单篇模式或批量模式，不再单独拆一个“筛选记录详情页”。</div>
                </div>
                <div class="section-meta">
                  <template v-if="selectedPaperIds.length > 1">已勾选 {{ selectedPaperIds.length }} 篇</template>
                  <template v-else-if="activeRow">{{ screeningDecisionLabel(activeRow.screeningDecision) }}</template>
                  <template v-else>未选择文献</template>
                </div>
              </div>

              <template v-if="selectedPaperIds.length > 1">
                <div class="mode-title">批量模式</div>
                <div class="summary-line">
                  <span>最终批量动作</span>
                  <strong>这里直接做最终决策；“已获取全文”和“最终排除”只影响最终报告入选，不会把初筛纳入/排除结果混在一起</strong>
                </div>
                <div class="action-grid">
                  <NButton type="success" :loading="batchUpdatingStatus === 'ready'" @click="markSelectedAsReady">批量标记已获取全文</NButton>
                  <NButton type="error" :loading="batchUpdatingStatus === 'excluded'" @click="excludeSelectedRows">批量最终排除</NButton>
                  <NButton tertiary :disabled="!selectedDoiUrls.length" @click="openSelectedDoiLinks">
                    批量打开 DOI
                    <template v-if="selectedDoiUrls.length">（{{ selectedDoiUrls.length }}）</template>
                  </NButton>
                </div>
                <div v-if="selectedIncludeMissingQueueCount" class="hint-line">
                  已勾选文献里有 {{ selectedIncludeMissingQueueCount }} 篇还没进入全文队列；点击“批量标记已获取全文”或“批量最终排除”时会先尝试自动同步全文队列。
                </div>
              </template>

              <template v-else-if="activeRow">
                <div class="mode-title">单篇模式</div>
                <div class="record-focus-title">{{ activeRow.title }}</div>
                <div class="focus-meta">
                  <span>{{ activeRow.year || '年份未知' }}</span>
                  <span>{{ activeRow.journal || '期刊未知' }}</span>
                  <span v-if="confidenceNumber(activeRow.confidence) !== null">
                    相关度 {{ Math.round((confidenceNumber(activeRow.confidence) ?? 0) * 100) }}%
                  </span>
                </div>

                <div class="abstract-block">
                  <div class="abstract-label">摘要</div>
                  <div class="abstract-panel">{{ activeRow.abstract || '当前记录没有可用摘要。' }}</div>
                </div>

                <NForm label-placement="top">
                  <NFormItem label="筛选判定">
                    <NSelect
                      v-model:value="activeDecision"
                      :options="[
                        { label: '纳入', value: 'include' },
                        { label: '剔除', value: 'exclude' },
                        { label: '不确定', value: 'uncertain' }
                      ]"
                    />
                  </NFormItem>
                  <NFormItem label="复核理由">
                    <NInput v-model:value="activeReason" type="textarea" :autosize="{ minRows: 4, maxRows: 8 }" />
                  </NFormItem>
                </NForm>
                <NButton type="primary" :loading="screeningSubmitting" @click="submitActiveReviewOverride">保存筛选判定</NButton>

                <div class="inspector-divider" />

                <template v-if="activeDecision === 'include'">
                  <div class="summary-line">
                    <span>全文阶段</span>
                    <strong>{{ activeRow.fulltextItem ? statusLabel(activeRow.fulltextStatus ?? 'pending') : '尚未同步到全文队列' }}</strong>
                  </div>
                  <div v-if="!activeRow.fulltextItem" class="hint-line">
                    这篇文献已经是“纳入”，但当前还没有出现在全文队列里。通常是全文来源还没同步，点下方按钮即可刷新。
                  </div>
                  <div class="toolbar-actions">
                    <NButton v-if="!activeRow.fulltextItem" type="primary" :loading="rebuildingQueue" @click="rebuildThreadFulltextQueue">
                      同步全文队列
                    </NButton>
                    <template v-else>
                      <NButton
                        :secondary="activeRow.fulltextStatus !== 'pending'"
                        :disabled="updatingPaperId === activeRow.paper_id && updatingStatus !== 'pending'"
                        :loading="updatingPaperId === activeRow.paper_id && updatingStatus === 'pending'"
                        @click="updateThreadFulltextStatus(activeRow, 'pending', activeFulltextNote)"
                      >
                        待处理全文
                      </NButton>
                      <NButton
                        type="success"
                        :secondary="activeRow.fulltextStatus !== 'ready'"
                        :disabled="updatingPaperId === activeRow.paper_id && updatingStatus !== 'ready'"
                        :loading="updatingPaperId === activeRow.paper_id && updatingStatus === 'ready'"
                        @click="updateThreadFulltextStatus(activeRow, 'ready', activeFulltextNote)"
                      >
                        已获取全文
                      </NButton>
                      <NButton
                        type="error"
                        :secondary="activeRow.fulltextStatus !== 'excluded'"
                        :disabled="updatingPaperId === activeRow.paper_id && updatingStatus !== 'excluded'"
                        :loading="updatingPaperId === activeRow.paper_id && updatingStatus === 'excluded'"
                        @click="updateThreadFulltextStatus(activeRow, 'excluded', activeFulltextNote)"
                      >
                        最终排除
                      </NButton>
                      <NButton
                        type="error"
                        :secondary="activeRow.fulltextStatus !== 'unavailable'"
                        :disabled="updatingPaperId === activeRow.paper_id && updatingStatus !== 'unavailable'"
                        :loading="updatingPaperId === activeRow.paper_id && updatingStatus === 'unavailable'"
                        @click="updateThreadFulltextStatus(activeRow, 'unavailable', activeFulltextNote)"
                      >
                        无权限获取
                      </NButton>
                      <NButton
                        type="warning"
                        :secondary="activeRow.fulltextStatus !== 'deferred'"
                        :disabled="updatingPaperId === activeRow.paper_id && updatingStatus !== 'deferred'"
                        :loading="updatingPaperId === activeRow.paper_id && updatingStatus === 'deferred'"
                        @click="updateThreadFulltextStatus(activeRow, 'deferred', activeFulltextNote)"
                      >
                        暂缓
                      </NButton>
                    </template>
                  </div>

                  <template v-if="activeRow.fulltextItem">
                    <NForm label-placement="top" style="margin-top: 14px;">
                      <NFormItem label="全文处理备注">
                        <NInput
                          v-model:value="activeFulltextNote"
                          type="textarea"
                          :autosize="{ minRows: 2, maxRows: 4 }"
                          placeholder="例如已在 Zotero 保存 / 通过机构权限获取 / 作为低优先级暂缓"
                        />
                      </NFormItem>
                    </NForm>
                    <div class="toolbar-actions">
                      <NButton tertiary @click="saveActiveFulltextNote" :disabled="updatingPaperId === activeRow.paper_id">
                        仅保存备注
                      </NButton>
                      <NButton text :disabled="!activeRow.doiUrl" @click="openExternal(activeRow.doiUrl)">打开 DOI</NButton>
                      <NButton text :disabled="!activeRow.doi" @click="copyDoi(activeRow.doi)">复制 DOI</NButton>
                      <NButton text :disabled="!activeRow.landingUrl" @click="openExternal(activeRow.landingUrl)">打开落地页</NButton>
                      <NButton text :disabled="!activeRow.pdfUrl" @click="openExternal(activeRow.pdfUrl)">打开 PDF</NButton>
                    </div>
                  </template>
                </template>
                <div v-else class="hint-line">
                  只有当前文献保持“纳入”时，才需要进入全文处理。改成“剔除”或“不确定”后，这条记录就会停在筛选阶段。
                </div>
              </template>

              <template v-else>
                <div class="empty-inspector">
                  <div class="mode-title">还没有选中文献</div>
                  <p>点左侧任意一篇进入单篇处理，或先勾选多篇再回到这里做批量改判 / 批量全文处理。</p>
                  <p>这次不会再默认替你选中第一篇，所以右侧保持空白，避免一进来就误以为系统已经帮你锁定了一条记录。</p>
                </div>
              </template>
            </NCard>

            <NCard class="panel-surface inspector-card" embedded>
              <div class="card-title-row">
                <div>
                  <div class="section-title">按标题或参考文献批量匹配</div>
                  <div class="section-copy">这里保留原来的高级批量能力，但不再单独占据一个筛选结果页面。</div>
                </div>
              </div>
              <NForm label-placement="top">
                <NFormItem label="批量判定结果">
                  <NSelect
                    v-model:value="batchReviewDecision"
                    :options="[
                      { label: '纳入', value: 'include' },
                      { label: '剔除', value: 'exclude' },
                      { label: '不确定', value: 'uncertain' }
                    ]"
                  />
                </NFormItem>
                <NFormItem label="批量审核理由">
                  <NInput v-model:value="batchReviewReason" />
                </NFormItem>
                <NFormItem label="标题或参考文献列表">
                  <NInput
                    v-model:value="bulkReviewText"
                    type="textarea"
                    :autosize="{ minRows: 6, maxRows: 12 }"
                    placeholder="支持整段参考文献列表，或一行一个标题"
                  />
                </NFormItem>
              </NForm>
              <NButton type="primary" secondary :loading="screeningSubmitting" :disabled="!bulkReviewText.trim()" @click="submitBulkReviewOverride">
                一键批量应用
              </NButton>
            </NCard>
          </div>
        </section>
      </div>

      <NEmpty v-else class="panel-surface empty-state" description="主题不存在或仍在加载中" />
    </NSpin>
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

.review-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px 24px;
  align-items: end;
  padding: 4px 0 2px;
  border-bottom: 1px solid rgba(90, 107, 93, 0.12);
}

.eyebrow {
  font-size: 12px;
  color: #6a776c;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.hero-main h1 {
  margin: 10px 0 8px;
  font-size: 34px;
  line-height: 1.12;
}

.hero-main p {
  margin: 0;
  color: #526055;
  line-height: 1.7;
  max-width: 920px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
  justify-self: end;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.overview-card,
.records-card,
.inspector-card {
  border-radius: 24px;
}

.card-title-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2520;
}

.section-copy,
.section-meta,
.batch-copy,
.summary-line,
.hint-line,
.record-meta,
.record-reason,
.record-abstract,
.focus-meta,
.empty-inspector p {
  color: #526055;
  line-height: 1.65;
}

.section-meta {
  white-space: nowrap;
}

.summary-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.summary-box {
  min-width: 96px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(247, 249, 246, 0.92);
  border: 1px solid rgba(90, 107, 93, 0.12);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-box span {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.summary-box strong {
  font-size: 28px;
  line-height: 1;
}

.summary-chip {
  border: 1px solid rgba(95, 108, 98, 0.18);
  background: rgba(255, 255, 255, 0.72);
  color: #304036;
  border-radius: 999px;
  padding: 9px 14px;
  font-size: 14px;
  cursor: pointer;
  transition: transform 140ms ease, border-color 140ms ease, background 140ms ease, box-shadow 140ms ease;
}

.summary-chip:hover {
  transform: translateY(-1px);
  border-color: rgba(45, 106, 79, 0.28);
}

.summary-chip.active {
  box-shadow: 0 10px 22px rgba(45, 106, 79, 0.14);
  border-color: rgba(45, 106, 79, 0.48);
  background: rgba(45, 106, 79, 0.12);
}

.summary-chip.success.active {
  background: rgba(47, 133, 90, 0.14);
  border-color: rgba(47, 133, 90, 0.42);
}

.summary-chip.error.active {
  background: rgba(192, 86, 33, 0.14);
  border-color: rgba(192, 86, 33, 0.42);
}

.summary-chip.warning.active {
  background: rgba(196, 137, 29, 0.14);
  border-color: rgba(196, 137, 29, 0.42);
}

.summary-line {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
}

.summary-line strong {
  color: #233126;
}

.hint-line {
  margin-top: 10px;
  color: #8a5b1f;
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(340px, 0.85fr);
  gap: 18px;
  align-items: start;
}

.records-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(240px, 0.7fr);
  gap: 12px;
  margin-top: 18px;
}

.batch-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-top: 14px;
}

.inline-alert {
  margin-top: 14px;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 18px;
}

.record-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  padding: 16px 18px;
  border-radius: 20px;
  border: 1px solid rgba(90, 107, 93, 0.12);
  background: rgba(255, 255, 255, 0.72);
  cursor: pointer;
  transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
}

.record-row:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 32px rgba(45, 106, 79, 0.08);
}

.record-row.active {
  border-color: rgba(45, 106, 79, 0.44);
  box-shadow: 0 18px 34px rgba(45, 106, 79, 0.14);
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

.record-head h2 {
  margin: 0;
  font-size: 20px;
  line-height: 1.4;
}

.record-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.record-meta {
  margin-top: 8px;
}

.record-reason {
  margin-top: 8px;
  white-space: pre-wrap;
}

.record-abstract {
  margin-top: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.record-quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 10px;
  align-items: center;
  margin-top: 12px;
}

.record-stage-copy {
  color: #526055;
  font-size: 13px;
}

.inspector-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.mode-title {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #708074;
  margin-top: 10px;
}

.record-focus-title {
  margin-top: 10px;
  font-size: 24px;
  line-height: 1.35;
  font-weight: 700;
}

.focus-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}

.abstract-block {
  margin-top: 14px;
}

.abstract-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #708074;
  margin-bottom: 8px;
}

.abstract-panel {
  border-radius: 14px;
  padding: 14px;
  background: rgba(247, 249, 246, 0.94);
  border: 1px solid rgba(71, 95, 76, 0.12);
  line-height: 1.65;
  white-space: pre-wrap;
}

.inspector-divider {
  height: 1px;
  margin: 18px 0;
  background: rgba(90, 107, 93, 0.12);
}

.action-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.empty-inspector {
  padding: 26px 0 10px;
}

.empty-inspector p {
  margin: 8px 0 0;
}

.empty-state {
  min-height: 180px;
  display: grid;
  place-items: center;
}

@media (max-width: 1220px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .workspace-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1080px) {
  .review-hero {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .hero-actions {
    justify-self: start;
    justify-content: flex-start;
  }

  .section-meta {
    white-space: normal;
  }

  .records-toolbar {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .card-title-row,
  .record-head,
  .summary-line {
    flex-direction: column;
  }

  .record-tags {
    justify-content: flex-start;
  }
}
</style>
