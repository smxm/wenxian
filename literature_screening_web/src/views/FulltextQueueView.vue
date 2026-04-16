<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { ArrowLeft, RefreshCw, Search, Wrench } from 'lucide-vue-next'
import {
  NButton,
  NCard,
  NCheckbox,
  NDivider,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSpin,
  NTabPane,
  NTabs,
  NTag,
  useMessage
} from 'naive-ui'
import {
  applyBulkReviewOverride,
  applyReviewOverride,
  applySelectionReviewOverride,
  enrichWorkbench as requestEnrichWorkbench,
  fetchTask,
  patchWorkbenchItem as requestPatchWorkbenchItem,
  patchWorkbenchItems as requestPatchWorkbenchItems,
  rebuildWorkbench as requestRebuildWorkbench
} from '@/api/client'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import type {
  ProjectDetail,
  TaskDetail,
  WorkbenchAccessStatus,
  WorkbenchCandidateItem,
  WorkbenchFinalDecision,
  WorkbenchStage,
  WorkbenchSummary
} from '@/types/api'

type WorkspaceTab = 'pool' | 'rounds'
type CandidateSort = 'stage' | 'updated' | 'year-desc' | 'year-asc'
type WorkflowFilter = 'all' | 'needs-screening' | 'needs-retrieval' | 'ready-for-decision' | 'completed'
type StageSummaryCountKey = keyof Pick<
  WorkbenchSummary,
  'needs_screening' | 'screened_out' | 'needs_link' | 'needs_access' | 'ready_for_decision' | 'report_included' | 'report_excluded' | 'unavailable' | 'deferred'
>

const route = useRoute()
const router = useRouter()
const message = useMessage()
const projectsStore = useProjectsStore()
const tasksStore = useTasksStore()

const projectId = computed(() => String(route.params.projectId))
const project = computed(() => projectsStore.currentProject)
const workbench = computed(() => project.value?.workbench ?? null)

const activeTab = ref<WorkspaceTab>('pool')
const searchKeyword = ref('')
const workflowFilter = ref<WorkflowFilter>('all')
const stageFilter = ref<'all' | WorkbenchStage>('all')
const languageFilter = ref<'all' | 'zh' | 'en' | 'unknown'>('all')
const screeningFilter = ref<'all' | 'include' | 'exclude' | 'uncertain' | 'none'>('all')
const roundFilter = ref<'all' | string>('all')
const linkFilter = ref<'all' | 'has-link' | 'missing-link'>('all')
const groupByStage = ref(false)
const showAdvancedFilters = ref(false)
const sortMode = ref<CandidateSort>('stage')
const selectedCandidateIds = ref<string[]>([])
const activeCandidateId = ref<string | null>(null)
const workbenchSubmitting = ref(false)
const rebuildingWorkbench = ref(false)
const enrichingWorkbench = ref(false)
const showAdvancedSettings = ref(false)
const sourceDatasetIds = ref<string[]>([])

const manualPreferredUrl = ref('')
const manualPdfUrl = ref('')
const accessNote = ref('')
const finalNote = ref('')

const selectedScreeningTaskId = ref<string | null>(null)
const screeningTaskDetail = ref<TaskDetail | null>(null)
const loadingScreeningTask = ref(false)
const screeningSubmitting = ref(false)
const roundSearch = ref('')
const roundDecisionFilter = ref<'all' | 'include' | 'exclude' | 'uncertain'>('all')
const activeRoundPaperId = ref<string | null>(null)
const selectedRoundPaperIds = ref<string[]>([])
const activeRoundDecision = ref<'include' | 'exclude' | 'uncertain'>('include')
const activeRoundReason = ref('')
const batchRoundDecision = ref<'include' | 'exclude' | 'uncertain'>('exclude')
const batchRoundReason = ref('人工复核：批量修正')
const bulkReviewText = ref('')

const stageMeta: Record<WorkbenchStage, { label: string; tone?: 'success' | 'error' | 'warning' | 'default' }> = {
  'needs-screening': { label: '待补筛选', tone: 'warning' },
  'screened-out': { label: '筛选已排除', tone: 'error' },
  'needs-link': { label: '待补链接', tone: 'warning' },
  'needs-access': { label: '待获取全文', tone: 'default' },
  'ready-for-decision': { label: '已获取待终判', tone: 'success' },
  'report-included': { label: '已纳入报告', tone: 'success' },
  'report-excluded': { label: '最终排除', tone: 'error' },
  unavailable: { label: '无权限获取', tone: 'error' },
  deferred: { label: '暂缓', tone: 'warning' }
}

const stageSummaryOrder: Array<{ key: WorkbenchStage; label: string; countKey: StageSummaryCountKey }> = [
  { key: 'needs-screening', label: '待补筛选', countKey: 'needs_screening' },
  { key: 'screened-out', label: '筛选已排除', countKey: 'screened_out' },
  { key: 'needs-link', label: '缺少链接', countKey: 'needs_link' },
  { key: 'needs-access', label: '待获取全文', countKey: 'needs_access' },
  { key: 'ready-for-decision', label: '待终判', countKey: 'ready_for_decision' },
  { key: 'report-included', label: '已纳入报告', countKey: 'report_included' },
  { key: 'report-excluded', label: '最终排除', countKey: 'report_excluded' },
  { key: 'unavailable', label: '无权限', countKey: 'unavailable' },
  { key: 'deferred', label: '暂缓', countKey: 'deferred' }
]

const screeningRounds = computed(() =>
  [...(project.value?.tasks ?? [])]
    .filter((task) => task.kind === 'screening' && task.status === 'succeeded')
    .sort((left, right) => dayjs(right.created_at).valueOf() - dayjs(left.created_at).valueOf())
)

const screeningRoundOrder = computed(() =>
  [...(project.value?.tasks ?? [])]
    .filter((task) => task.kind === 'screening')
    .sort((left, right) => dayjs(left.created_at).valueOf() - dayjs(right.created_at).valueOf())
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
      label: `第 ${roundIndex} 轮 · ${task.title}`,
      value: task.id
    }
  })
])

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
    description: '打开链接'
  },
  {
    key: 'ready-for-decision' as WorkflowFilter,
    label: '待终判',
    count: workbenchSummary.value.ready_for_decision,
    description: '做终判'
  },
  {
    key: 'completed' as WorkflowFilter,
    label: '已完成',
    count: workbenchSummary.value.report_included + workbenchSummary.value.report_excluded,
    description: '已处理'
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
const activeCandidate = computed(() => (activeCandidateId.value ? candidateMap.value.get(activeCandidateId.value) ?? null : null))
const selectedCandidateIdSet = computed(() => new Set(selectedCandidateIds.value))
const selectedCandidates = computed(() =>
  selectedCandidateIds.value
    .map((candidateId) => candidateMap.value.get(candidateId))
    .filter((item): item is WorkbenchCandidateItem => Boolean(item))
)

const inspectorMode = computed<'empty' | 'single' | 'batch'>(() => {
  if (selectedCandidateIds.value.length > 1) return 'batch'
  if (activeCandidate.value) return 'single'
  return 'empty'
})

const selectedCandidatePreview = computed(() => selectedCandidates.value.slice(0, 5))
const selectedCandidateOverflowCount = computed(() => Math.max(selectedCandidates.value.length - selectedCandidatePreview.value.length, 0))

const filteredCandidates = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return workbenchItems.value
    .filter((item) => {
      if (workflowFilter.value === 'needs-screening' && item.stage !== 'needs-screening') return false
      if (workflowFilter.value === 'needs-retrieval' && !['needs-link', 'needs-access'].includes(item.stage)) return false
      if (workflowFilter.value === 'ready-for-decision' && item.stage !== 'ready-for-decision') return false
      if (workflowFilter.value === 'completed' && !['report-included', 'report-excluded'].includes(item.stage)) return false
      if (stageFilter.value !== 'all' && item.stage !== stageFilter.value) return false
      if (languageFilter.value !== 'all' && item.language !== languageFilter.value) return false
      if (screeningFilter.value !== 'all') {
        if (screeningFilter.value === 'none' && item.latest_screening_decision) return false
        if (screeningFilter.value !== 'none' && item.latest_screening_decision !== screeningFilter.value) return false
      }
      if (roundFilter.value !== 'all' && !item.screening_history.some((history) => history.task_id === roundFilter.value)) return false
      if (linkFilter.value === 'has-link' && !item.preferred_open_url && !item.preferred_pdf_url) return false
      if (linkFilter.value === 'missing-link' && (item.preferred_open_url || item.preferred_pdf_url)) return false
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
      if (sortMode.value === 'updated') return dayjs(right.updated_at).valueOf() - dayjs(left.updated_at).valueOf()
      if (sortMode.value === 'year-asc') return (left.year ?? Infinity) - (right.year ?? Infinity)
      if (sortMode.value === 'year-desc') return (right.year ?? -Infinity) - (left.year ?? -Infinity)
      const stageOrder: WorkbenchStage[] = [
        'needs-screening',
        'needs-link',
        'needs-access',
        'ready-for-decision',
        'report-included',
        'report-excluded',
        'unavailable',
        'deferred',
        'screened-out'
      ]
      const leftIndex = stageOrder.indexOf(left.stage)
      const rightIndex = stageOrder.indexOf(right.stage)
      if (leftIndex !== rightIndex) return leftIndex - rightIndex
      return (right.year ?? -Infinity) - (left.year ?? -Infinity)
    })
})

const groupedCandidates = computed(() => {
  const groups = new Map<WorkbenchStage, WorkbenchCandidateItem[]>()
  for (const item of filteredCandidates.value) {
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

const reportEligibleSelectedCount = computed(() =>
  selectedCandidates.value.filter((item) => canIncludeInReport(item)).length
)

const roundTaskOptions = computed(() =>
  screeningRounds.value.map((task) => {
    const roundIndex = screeningRoundOrder.value.findIndex((item) => item.id === task.id) + 1
    const summary = task.summary ?? {}
    return {
      label: `第 ${roundIndex} 轮 · 纳入 ${Number(summary.included_count ?? 0)} / 剔除 ${Number(summary.excluded_count ?? 0)} / 不确定 ${Number(summary.uncertain_count ?? 0)}`,
      value: task.id
    }
  })
)

const selectedRoundTaskLabel = computed(
  () => roundTaskOptions.value.find((item) => item.value === selectedScreeningTaskId.value)?.label ?? '未选择筛选轮次'
)

const selectedRoundSummary = computed(() => {
  const summary = screeningTaskDetail.value?.summary ?? {}
  return {
    included: Number(summary.included_count ?? 0),
    excluded: Number(summary.excluded_count ?? 0),
    uncertain: Number(summary.uncertain_count ?? 0),
    processed: Number(summary.processed_count ?? 0)
  }
})

const filteredRoundRows = computed(() => {
  const keyword = roundSearch.value.trim().toLowerCase()
  return (screeningTaskDetail.value?.records ?? [])
    .filter((row) => {
      if (roundDecisionFilter.value !== 'all' && row.decision !== roundDecisionFilter.value) return false
      if (!keyword) return true
      const haystack = [row.title, row.journal, row.doi, row.reason, row.abstract].filter(Boolean).join(' ').toLowerCase()
      return haystack.includes(keyword)
    })
    .slice()
    .sort((left, right) => (right.year ?? -Infinity) - (left.year ?? -Infinity))
})

const roundRowMap = computed(() => new Map((screeningTaskDetail.value?.records ?? []).map((row) => [row.paper_id, row])))
const activeRoundRow = computed(() => (activeRoundPaperId.value ? roundRowMap.value.get(activeRoundPaperId.value) ?? null : null))
const selectedRoundIdSet = computed(() => new Set(selectedRoundPaperIds.value))

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
      return '尚未终判'
  }
}

function candidateNeedsRoundReview(item: WorkbenchCandidateItem) {
  return item.latest_screening_decision === 'exclude' || item.latest_screening_decision === 'uncertain'
}

function canIncludeInReport(item: WorkbenchCandidateItem) {
  return !candidateNeedsRoundReview(item) && item.access_status === 'ready'
}

function setWorkflowFilter(nextFilter: WorkflowFilter) {
  workflowFilter.value = nextFilter
  stageFilter.value = 'all'
}

function stageParentWorkflow(stage: WorkbenchStage): WorkflowFilter {
  if (stage === 'needs-screening') return 'needs-screening'
  if (stage === 'needs-link' || stage === 'needs-access') return 'needs-retrieval'
  if (stage === 'ready-for-decision') return 'ready-for-decision'
  if (stage === 'report-included' || stage === 'report-excluded') return 'completed'
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

function candidateSummary(item: WorkbenchCandidateItem) {
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

function initializeRoundSelection() {
  const validIds = new Set((screeningTaskDetail.value?.records ?? []).map((row) => row.paper_id))
  selectedRoundPaperIds.value = selectedRoundPaperIds.value.filter((paperId) => validIds.has(paperId))
  if (activeRoundPaperId.value && !validIds.has(activeRoundPaperId.value)) {
    activeRoundPaperId.value = null
  }
}

function applyRouteIntent() {
  const requestedTab = typeof route.query.tab === 'string' ? route.query.tab : null
  activeTab.value = requestedTab === 'rounds' ? 'rounds' : 'pool'
  const requestedWorkflow = typeof route.query.workflow === 'string' ? route.query.workflow : null
  if (requestedWorkflow && ['all', 'needs-screening', 'needs-retrieval', 'ready-for-decision', 'completed'].includes(requestedWorkflow)) {
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
  const validTaskIds = new Set(roundTaskOptions.value.map((item) => item.value))
  if (requestedTaskId && validTaskIds.has(requestedTaskId)) {
    selectedScreeningTaskId.value = requestedTaskId
  } else if (!selectedScreeningTaskId.value || !validTaskIds.has(selectedScreeningTaskId.value)) {
    selectedScreeningTaskId.value = roundTaskOptions.value[0]?.value ?? null
  }
}

async function replaceRouteState() {
  await router.replace({
    query: {
      ...route.query,
      tab: activeTab.value === 'pool' ? undefined : activeTab.value,
      workflow: workflowFilter.value === 'all' ? undefined : workflowFilter.value,
      stage: stageFilter.value === 'all' ? undefined : stageFilter.value,
      screeningTaskId: selectedScreeningTaskId.value ?? undefined
    }
  })
}

async function loadScreeningTask(taskId: string | null) {
  if (!taskId) {
    screeningTaskDetail.value = null
    initializeRoundSelection()
    return
  }
  loadingScreeningTask.value = true
  try {
    screeningTaskDetail.value = await fetchTask(taskId)
    initializeRoundSelection()
  } catch (error) {
    message.error(extractErrorMessage(error, '筛选轮次加载失败'))
  } finally {
    loadingScreeningTask.value = false
  }
}

async function loadProject() {
  await projectsStore.loadProject(projectId.value)
  initializeWorkbenchState()
  applyRouteIntent()
  if (activeTab.value === 'rounds') {
    await loadScreeningTask(selectedScreeningTaskId.value)
  }
  initializeCandidateSelection()
}

watch(
  projectId,
  async () => {
    searchKeyword.value = ''
    selectedCandidateIds.value = []
    activeCandidateId.value = null
    selectedRoundPaperIds.value = []
    activeRoundPaperId.value = null
    await loadProject()
  },
  { immediate: true }
)

watch(
  () => [route.query.tab, route.query.workflow, route.query.stage, route.query.screeningTaskId],
  async () => {
    if (!project.value) return
    applyRouteIntent()
    if (activeTab.value === 'rounds') {
      await loadScreeningTask(selectedScreeningTaskId.value)
    }
  }
)

watch(workbench, () => {
  initializeWorkbenchState()
  initializeCandidateSelection()
})

watch(activeCandidate, (item) => {
  manualPreferredUrl.value = item?.preferred_open_url ?? ''
  manualPdfUrl.value = item?.preferred_pdf_url ?? ''
  accessNote.value = item?.access_note ?? ''
  finalNote.value = item?.final_note ?? ''
})

watch(activeRoundRow, (row) => {
  activeRoundDecision.value = (row?.decision as 'include' | 'exclude' | 'uncertain') ?? 'include'
  activeRoundReason.value = row?.reason ?? ''
})

watch(activeTab, async (nextTab) => {
  await replaceRouteState()
  if (nextTab === 'rounds' && selectedScreeningTaskId.value && selectedScreeningTaskId.value !== screeningTaskDetail.value?.id) {
    await loadScreeningTask(selectedScreeningTaskId.value)
  }
})

watch(selectedScreeningTaskId, async (nextTaskId, previousTaskId) => {
  if (!nextTaskId || nextTaskId === previousTaskId || activeTab.value !== 'rounds') return
  await replaceRouteState()
  await loadScreeningTask(nextTaskId)
})

watch(
  [workflowFilter, stageFilter],
  async () => {
    if (!project.value || activeTab.value !== 'pool') return
    await replaceRouteState()
  }
)

function setActiveCandidate(candidateId: string) {
  activeCandidateId.value = candidateId
}

function toggleCandidateSelected(candidateId: string, checked: boolean) {
  if (checked) {
    if (!selectedCandidateIdSet.value.has(candidateId)) {
      selectedCandidateIds.value = [...selectedCandidateIds.value, candidateId]
    }
    if (!activeCandidateId.value) activeCandidateId.value = candidateId
    return
  }
  selectedCandidateIds.value = selectedCandidateIds.value.filter((item) => item !== candidateId)
}

function toggleSelectAllCandidates() {
  const visibleIds = filteredCandidates.value.map((item) => item.candidate_id)
  const allSelected = visibleIds.length > 0 && visibleIds.every((candidateId) => selectedCandidateIdSet.value.has(candidateId))
  if (allSelected) {
    const visibleSet = new Set(visibleIds)
    selectedCandidateIds.value = selectedCandidateIds.value.filter((candidateId) => !visibleSet.has(candidateId))
    return
  }
  selectedCandidateIds.value = Array.from(new Set([...selectedCandidateIds.value, ...visibleIds]))
  if (!activeCandidateId.value) activeCandidateId.value = visibleIds[0] ?? null
}

function setActiveRoundRow(paperId: string) {
  activeRoundPaperId.value = paperId
}

function toggleRoundRowSelected(paperId: string, checked: boolean) {
  if (checked) {
    if (!selectedRoundIdSet.value.has(paperId)) {
      selectedRoundPaperIds.value = [...selectedRoundPaperIds.value, paperId]
    }
    if (!activeRoundPaperId.value) activeRoundPaperId.value = paperId
    return
  }
  selectedRoundPaperIds.value = selectedRoundPaperIds.value.filter((item) => item !== paperId)
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
  groupByStage.value = false
  sortMode.value = 'stage'
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

async function patchSingleCandidate(payload: {
  access_status?: WorkbenchAccessStatus | null
  final_decision?: WorkbenchFinalDecision | null
  access_note?: string | null
  final_note?: string | null
  preferred_open_url?: string | null
  preferred_pdf_url?: string | null
}) {
  if (!project.value || !activeCandidate.value) return
  workbenchSubmitting.value = true
  try {
    const updatedProject = await requestPatchWorkbenchItem(project.value.id, activeCandidate.value.candidate_id, payload)
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

async function saveActiveLinks() {
  await patchSingleCandidate({
    preferred_open_url: manualPreferredUrl.value.trim() || '',
    preferred_pdf_url: manualPdfUrl.value.trim() || ''
  })
}

async function saveActiveNotes() {
  await patchSingleCandidate({
    access_note: accessNote.value,
    final_note: finalNote.value
  })
}

async function setActiveAccessStatus(status: WorkbenchAccessStatus) {
  await patchSingleCandidate({
    access_status: status,
    access_note: accessNote.value
  })
}

async function setActiveFinalDecision(decision: WorkbenchFinalDecision) {
  if (decision === 'include' && activeCandidate.value && !canIncludeInReport(activeCandidate.value)) {
    if (candidateNeedsRoundReview(activeCandidate.value)) {
      message.warning('当前最新筛选结论不是“纳入”，请先到“轮次复核”里修正，再终判为纳入报告。')
      return
    }
    message.warning('只有已经拿到全文的文献，才能终判为纳入报告。')
    return
  }
  await patchSingleCandidate({
    final_decision: decision,
    final_note: finalNote.value
  })
}

async function markSelectedReportIncluded() {
  if (!selectedCandidateIds.value.length) return
  if (reportEligibleSelectedCount.value !== selectedCandidateIds.value.length) {
    message.warning('只有未被最新筛选结论排除、且已经拿到全文的文献，才能批量终判为纳入报告。')
    return
  }
  await patchSelectedCandidates({ final_decision: 'include' })
}

async function refreshAfterRoundReview(taskDetail: TaskDetail) {
  screeningTaskDetail.value = taskDetail
  await Promise.all([projectsStore.loadProject(projectId.value), tasksStore.refreshList()])
  initializeWorkbenchState()
  initializeCandidateSelection()
  initializeRoundSelection()
}

async function saveActiveRoundReview() {
  if (!screeningTaskDetail.value || !activeRoundRow.value) return
  screeningSubmitting.value = true
  try {
    const updated = await applyReviewOverride(screeningTaskDetail.value.id, {
      paper_id: activeRoundRow.value.paper_id,
      decision: activeRoundDecision.value,
      reason: activeRoundReason.value
    })
    await refreshAfterRoundReview(updated)
    message.success('本轮筛选判定已保存')
  } catch (error) {
    message.error(extractErrorMessage(error, '筛选判定保存失败'))
  } finally {
    screeningSubmitting.value = false
  }
}

async function saveSelectedRoundReview() {
  if (!screeningTaskDetail.value || !selectedRoundPaperIds.value.length) return
  screeningSubmitting.value = true
  try {
    const updated = await applySelectionReviewOverride(screeningTaskDetail.value.id, {
      paper_ids: [...selectedRoundPaperIds.value],
      decision: batchRoundDecision.value,
      reason: batchRoundReason.value
    })
    await refreshAfterRoundReview(updated)
    message.success('已按所选文献批量改判')
    selectedRoundPaperIds.value = []
  } catch (error) {
    message.error(extractErrorMessage(error, '批量改判失败'))
  } finally {
    screeningSubmitting.value = false
  }
}

async function submitBulkRoundReview() {
  if (!screeningTaskDetail.value || !bulkReviewText.value.trim()) return
  screeningSubmitting.value = true
  try {
    const updated = await applyBulkReviewOverride(screeningTaskDetail.value.id, {
      entries_text: bulkReviewText.value,
      decision: batchRoundDecision.value,
      reason: batchRoundReason.value
    })
    await refreshAfterRoundReview(updated)
    bulkReviewText.value = ''
    message.success('标题 / 参考文献匹配改判已应用')
  } catch (error) {
    message.error(extractErrorMessage(error, '批量匹配失败'))
  } finally {
    screeningSubmitting.value = false
  }
}
</script>

<template>
  <div class="review-page">
    <NSpin :show="projectsStore.loadingDetail && !project">
      <div v-if="project" class="review-stack">
        <section class="review-hero">
          <div class="hero-main">
            <div class="eyebrow">Candidate Workbench</div>
            <h1>候选文献工作台</h1>
            <p>找文献、开链接、标状态、做终判。</p>
          </div>
          <div class="hero-actions">
            <RouterLink :to="`/threads/${project.id}`">
              <NButton secondary>
                <template #icon><ArrowLeft :size="16" /></template>
                返回主题页
              </NButton>
            </RouterLink>
            <NButton secondary @click="activeTab = activeTab === 'pool' ? 'rounds' : 'pool'">
              {{ activeTab === 'pool' ? '回到轮次复核' : '回到候选池' }}
            </NButton>
          </div>
        </section>

        <NTabs v-model:value="activeTab" type="segment" animated>
          <NTabPane name="pool" tab="候选池">
            <section class="workspace-grid">
              <div class="candidate-main-stack">
                <NCard class="panel-surface overview-card focus-board" embedded>
                  <div class="card-title-row">
                    <div>
                      <div class="section-title">先处理这些步骤</div>
                      <div class="section-copy">按顺序处理即可。</div>
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

                <NCard class="panel-surface records-card" embedded>
                  <div class="card-title-row">
                    <div>
                      <div class="section-title">项目候选文献池</div>
                      <div class="section-copy">左边选文献，右边处理。</div>
                    </div>
                    <div class="section-meta">{{ activeWorkflowLabel }} · {{ filteredCandidates.length }} / {{ workbenchItems.length }} 篇</div>
                  </div>

                  <div class="records-toolbar compact-toolbar">
                    <NInput v-model:value="searchKeyword" placeholder="搜标题、期刊、DOI 或轮次来源">
                      <template #prefix><Search :size="16" /></template>
                    </NInput>
                    <NSelect v-model:value="roundFilter" :options="roundFilterOptions" />
                  </div>

                  <div class="filter-actions">
                    <NButton tertiary @click="showAdvancedFilters = !showAdvancedFilters">
                      {{ showAdvancedFilters ? '收起高级筛选' : '更多筛选' }}
                    </NButton>
                    <NButton tertiary @click="groupByStage = !groupByStage">
                      {{ groupByStage ? '切回普通列表' : '按阶段分组看' }}
                    </NButton>
                    <NButton tertiary :disabled="!filteredCandidates.length || workbenchSubmitting" @click="toggleSelectAllCandidates">
                      {{ filteredCandidates.length && filteredCandidates.every((item) => selectedCandidateIdSet.has(item.candidate_id)) ? '取消全选当前结果' : '全选当前结果' }}
                    </NButton>
                    <NButton tertiary @click="clearPoolFilters">清空筛选</NButton>
                    <NButton tertiary @click="showAdvancedSettings = !showAdvancedSettings">
                      <template #icon><Wrench :size="16" /></template>
                      {{ showAdvancedSettings ? '收起来源设置' : '来源与同步' }}
                    </NButton>
                  </div>

                  <div v-if="showAdvancedFilters" class="filter-drawer">
                    <div class="drawer-grid">
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
                      <NSelect
                        v-model:value="sortMode"
                        :options="[
                          { label: '按阶段', value: 'stage' },
                          { label: '按最近更新', value: 'updated' },
                          { label: '按年份从新到旧', value: 'year-desc' },
                          { label: '按年份从旧到新', value: 'year-asc' }
                        ]"
                      />
                    </div>
                  </div>

                  <div v-if="showAdvancedSettings" class="filter-drawer source-drawer">
                    <div class="drawer-title">候选来源与同步</div>
                    <div class="section-copy">切换来源后会重建候选池。</div>
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

                  <div v-if="selectedCandidateIds.length" class="selection-toolbar">
                    <div class="selection-summary">
                      <strong>已选 {{ selectedCandidateIds.length }} 篇</strong>
                      <span>批量动作只作用于已勾选文献。处理完以后会自动刷新项目候选池。</span>
                    </div>
                    <div class="selection-actions">
                      <NButton secondary size="small" :disabled="!filteredCandidates.length || workbenchSubmitting" @click="toggleSelectAllCandidates">
                        {{ filteredCandidates.length && filteredCandidates.every((item) => selectedCandidateIdSet.has(item.candidate_id)) ? '取消全选当前结果' : '全选当前结果' }}
                      </NButton>
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
                      <NButton type="success" size="small" :disabled="!selectedCandidateIds.length || workbenchSubmitting || reportEligibleSelectedCount !== selectedCandidateIds.length" :loading="workbenchSubmitting" @click="markSelectedReportIncluded">
                        纳入报告
                      </NButton>
                      <NButton type="error" size="small" :disabled="!selectedCandidateIds.length || workbenchSubmitting" :loading="workbenchSubmitting" @click="patchSelectedCandidates({ final_decision: 'exclude' })">
                        最终排除
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
                                <div class="record-meta">{{ item.journal || '未知期刊' }} · {{ item.source_round_labels.join('、') || '未关联轮次' }}</div>
                              </div>
                              <div class="record-tags">
                                <NTag round size="small" :type="stageTagType(item.stage)">{{ stageLabel(item.stage) }}</NTag>
                                <NTag round size="small">{{ item.year ?? '----' }}</NTag>
                              </div>
                            </div>
                            <div class="record-reason">{{ candidateSummary(item) }}</div>
                            <div class="record-quick-actions">
                              <span class="record-stage-copy">{{ finalDecisionLabel(item.final_decision) }} · {{ accessStatusLabel(item.access_status) }}</span>
                              <NButton v-if="item.preferred_open_url" secondary size="small" @click.stop="openExternal(item.preferred_open_url)">打开链接</NButton>
                              <NButton v-if="item.preferred_pdf_url" text size="small" @click.stop="openExternal(item.preferred_pdf_url)">PDF</NButton>
                              <NButton
                                v-if="item.links.some((link) => link.kind === 'doi')"
                                text
                                size="small"
                                @click.stop="openExternal(item.links.find((link) => link.kind === 'doi')?.url ?? null)"
                              >
                                DOI
                              </NButton>
                            </div>
                          </div>
                        </article>
                      </section>
                    </div>
                    <NEmpty v-else class="empty-state" description="当前筛选条件下没有匹配文献" />
                  </template>

                  <div v-else-if="filteredCandidates.length" class="record-list">
                    <article
                      v-for="item in filteredCandidates"
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
                            <div class="record-meta">{{ item.journal || '未知期刊' }} · {{ item.source_round_labels.join('、') || '未关联轮次' }}</div>
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
                          <NButton v-if="item.preferred_open_url" secondary size="small" @click.stop="openExternal(item.preferred_open_url)">打开链接</NButton>
                          <NButton v-if="item.preferred_pdf_url" text size="small" @click.stop="openExternal(item.preferred_pdf_url)">PDF</NButton>
                          <NButton
                            v-if="item.links.some((link) => link.kind === 'doi')"
                            text
                            size="small"
                            @click.stop="openExternal(item.links.find((link) => link.kind === 'doi')?.url ?? null)"
                          >
                            DOI
                          </NButton>
                        </div>
                      </div>
                    </article>
                  </div>

                  <NEmpty v-else class="empty-state" description="当前筛选条件下没有匹配文献" />
                </NCard>
              </div>

              <div class="inspector-stack">
                <NCard class="panel-surface inspector-card" embedded>
                  <template v-if="inspectorMode === 'batch'">
                    <div class="mode-badge">Batch Mode</div>
                    <div class="card-title-row">
                      <div>
                        <div class="section-title">正在批量处理</div>
                        <div class="section-copy">操作会作用到全部勾选项。</div>
                      </div>
                      <div class="section-meta">已选 {{ selectedCandidateIds.length }} 篇</div>
                    </div>
                    <div class="summary-strip">
                      <div class="summary-box"><span>可直接纳入报告</span><strong>{{ reportEligibleSelectedCount }}</strong></div>
                      <div class="summary-box"><span>可打开链接</span><strong>{{ selectedPreferredUrls.length }}</strong></div>
                      <div class="summary-box"><span>有 PDF</span><strong>{{ selectedPdfUrls.length }}</strong></div>
                    </div>
                    <div class="selection-preview">
                      <div v-for="item in selectedCandidatePreview" :key="item.candidate_id" class="preview-row">
                        <strong>{{ item.title }}</strong>
                        <span>{{ stageLabel(item.stage) }} · {{ accessStatusLabel(item.access_status) }}</span>
                      </div>
                      <div v-if="selectedCandidateOverflowCount" class="hint-line">
                        还有 {{ selectedCandidateOverflowCount }} 篇未展开显示。
                      </div>
                    </div>
                  </template>

                  <template v-else-if="activeCandidate">
                    <div class="mode-badge">Single Review</div>
                    <div class="card-title-row">
                      <div>
                        <div class="section-title">单篇处理</div>
                        <div class="section-copy">先开链接，再标状态，再做终判。</div>
                      </div>
                      <div class="section-meta">{{ stageLabel(activeCandidate.stage) }}</div>
                    </div>
                    <div class="record-focus-title">{{ activeCandidate.title }}</div>
                    <div class="focus-meta">
                      <span>{{ activeCandidate.year || '年份未知' }}</span>
                      <span>{{ activeCandidate.journal || '期刊未知' }}</span>
                      <span>{{ activeCandidate.language === 'zh' ? '中文' : activeCandidate.language === 'en' ? '英文' : '语言未知' }}</span>
                    </div>
                    <div class="detail-grid compact-detail-grid">
                      <div class="detail-block">
                        <div class="detail-label">当前筛选状态</div>
                        <div class="detail-value">
                          <NTag round :type="screeningDecisionType(activeCandidate.latest_screening_decision)">
                            {{ screeningDecisionLabel(activeCandidate.latest_screening_decision) }}
                          </NTag>
                        </div>
                      </div>
                      <div class="detail-block">
                        <div class="detail-label">来源轮次</div>
                        <div class="detail-copy">{{ activeCandidate.source_round_labels.join('、') || '尚未匹配轮次' }}</div>
                      </div>
                    </div>

                    <section class="step-card">
                      <div class="step-index">1</div>
                      <div class="step-body">
                        <div class="step-head">
                          <div>
                            <div class="step-title">先打开链接</div>
                            <div class="step-copy">优先使用首选链接。中文文献会正常保留落地页，不再只依赖 DOI。</div>
                          </div>
                          <NTag round :type="activeCandidate.preferred_open_url || activeCandidate.preferred_pdf_url ? 'success' : 'warning'">
                            {{ activeCandidate.preferred_open_url || activeCandidate.preferred_pdf_url ? '已有可用链接' : '需要补链接' }}
                          </NTag>
                        </div>
                        <div class="action-grid">
                          <NButton type="primary" secondary :disabled="!activeCandidate.preferred_open_url" @click="openExternal(activeCandidate.preferred_open_url)">
                            打开首选链接
                          </NButton>
                          <NButton tertiary :disabled="!activeCandidate.preferred_pdf_url" @click="openExternal(activeCandidate.preferred_pdf_url)">
                            打开 PDF
                          </NButton>
                          <NButton
                            tertiary
                            :disabled="!activeCandidate.links.some((link) => link.kind === 'doi')"
                            @click="openExternal(activeCandidate.links.find((link) => link.kind === 'doi')?.url ?? null)"
                          >
                            打开 DOI
                          </NButton>
                        </div>
                        <details class="fold-panel">
                          <summary>补充或修正链接</summary>
                          <div class="fold-body">
                            <div class="link-stack">
                              <div v-for="link in activeCandidate.links" :key="`${link.kind}-${link.url}`" class="link-row">
                                <span>{{ link.label }}</span>
                                <div class="link-actions">
                                  <a class="plain-link" :href="link.url" target="_blank" rel="noopener">{{ link.url }}</a>
                                </div>
                              </div>
                              <div v-if="!activeCandidate.links.length" class="hint-line">当前还没有可用链接，建议先补充手工首选链接。</div>
                            </div>
                            <NForm label-placement="top">
                              <NFormItem label="手工首选链接">
                                <NInput v-model:value="manualPreferredUrl" placeholder="优先用于一键打开的链接；中文文献可直接填 CNKI / 万方落地页" />
                              </NFormItem>
                              <NFormItem label="手工 PDF 链接">
                                <NInput v-model:value="manualPdfUrl" placeholder="可直接下载的 PDF 链接；留空则不覆盖当前值" />
                              </NFormItem>
                            </NForm>
                            <NButton tertiary :loading="workbenchSubmitting" @click="saveActiveLinks">保存手工链接</NButton>
                          </div>
                        </details>
                      </div>
                    </section>

                    <section class="step-card">
                      <div class="step-index">2</div>
                      <div class="step-body">
                        <div class="step-head">
                          <div>
                            <div class="step-title">再标记全文状态</div>
                            <div class="step-copy">把“是否已经拿到全文”这一步处理清楚，后面终判才会更顺。</div>
                          </div>
                          <NTag round :type="activeCandidate.access_status === 'ready' ? 'success' : activeCandidate.access_status === 'unavailable' ? 'error' : activeCandidate.access_status === 'deferred' ? 'warning' : 'default'">
                            {{ accessStatusLabel(activeCandidate.access_status) }}
                          </NTag>
                        </div>
                        <div class="action-grid">
                          <NButton :secondary="activeCandidate.access_status !== 'pending'" :loading="workbenchSubmitting" @click="setActiveAccessStatus('pending')">待获取</NButton>
                          <NButton type="success" :secondary="activeCandidate.access_status !== 'ready'" :loading="workbenchSubmitting" @click="setActiveAccessStatus('ready')">已获取全文</NButton>
                          <NButton type="error" :secondary="activeCandidate.access_status !== 'unavailable'" :loading="workbenchSubmitting" @click="setActiveAccessStatus('unavailable')">无权限</NButton>
                          <NButton type="warning" :secondary="activeCandidate.access_status !== 'deferred'" :loading="workbenchSubmitting" @click="setActiveAccessStatus('deferred')">暂缓</NButton>
                        </div>
                        <NForm label-placement="top">
                          <NFormItem label="全文处理备注">
                            <NInput v-model:value="accessNote" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" placeholder="例如：已在 Zotero 保存 / 需要机构权限 / 等待补链" />
                          </NFormItem>
                        </NForm>
                        <NButton tertiary :loading="workbenchSubmitting" @click="saveActiveNotes">保存当前备注</NButton>
                      </div>
                    </section>

                    <section class="step-card">
                      <div class="step-index">3</div>
                      <div class="step-body">
                        <div class="step-head">
                          <div>
                            <div class="step-title">最后决定是否进入报告</div>
                            <div class="step-copy">只有全文到手以后，才建议终判是否进入报告。</div>
                          </div>
                          <NTag round :type="activeCandidate.final_decision === 'include' ? 'success' : activeCandidate.final_decision === 'exclude' ? 'error' : activeCandidate.final_decision === 'deferred' ? 'warning' : 'default'">
                            {{ finalDecisionLabel(activeCandidate.final_decision) }}
                          </NTag>
                        </div>
                        <div class="action-grid">
                          <NButton
                            type="success"
                            :secondary="activeCandidate.final_decision !== 'include'"
                            :loading="workbenchSubmitting"
                            :disabled="!canIncludeInReport(activeCandidate)"
                            @click="setActiveFinalDecision('include')"
                          >
                            纳入报告
                          </NButton>
                          <NButton type="error" :secondary="activeCandidate.final_decision !== 'exclude'" :loading="workbenchSubmitting" @click="setActiveFinalDecision('exclude')">
                            最终排除
                          </NButton>
                          <NButton type="warning" :secondary="activeCandidate.final_decision !== 'deferred'" :loading="workbenchSubmitting" @click="setActiveFinalDecision('deferred')">
                            暂不决定
                          </NButton>
                          <NButton :secondary="activeCandidate.final_decision !== 'undecided'" :loading="workbenchSubmitting" @click="setActiveFinalDecision('undecided')">
                            取消终判
                          </NButton>
                        </div>
                        <div v-if="candidateNeedsRoundReview(activeCandidate)" class="hint-line">
                          当前最新筛选结论不是“纳入”，如果要修正，请切到“轮次复核”页签处理。
                        </div>
                        <div v-else-if="activeCandidate.access_status !== 'ready'" class="hint-line">
                          只有拿到全文后，才会开放“纳入报告”。
                        </div>
                        <div v-else-if="!activeCandidate.latest_screening_decision" class="hint-line">
                          这篇候选暂时还没有匹配到轮次历史，但它仍然可以作为项目级候选文献继续处理。
                        </div>
                        <NForm label-placement="top">
                          <NFormItem label="最终去留备注">
                            <NInput v-model:value="finalNote" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" placeholder="例如：最终保留用于报告 / 内容偏离研究问题" />
                          </NFormItem>
                        </NForm>
                        <NButton tertiary :loading="workbenchSubmitting" @click="saveActiveNotes">保存当前备注</NButton>
                      </div>
                    </section>

                    <details class="fold-panel">
                      <summary>查看筛选历史</summary>
                      <div class="fold-body">
                        <div v-if="activeCandidate.screening_history.length" class="history-stack">
                          <div v-for="history in activeCandidate.screening_history" :key="`${history.task_id}-${history.paper_id}`" class="history-row">
                            <div class="history-head">
                              <strong>{{ history.round_index ? `第 ${history.round_index} 轮` : history.task_title || history.task_id }}</strong>
                              <NTag round size="small" :type="screeningDecisionType(history.decision)">{{ screeningDecisionLabel(history.decision) }}</NTag>
                            </div>
                            <div class="history-copy">{{ history.reason || '未填写理由' }}</div>
                          </div>
                        </div>
                        <div v-else class="hint-line">当前候选文献还没有匹配到筛选历史。</div>
                      </div>
                    </details>
                  </template>

                  <div v-else class="empty-inspector">
                    <div class="mode-badge">Quick Start</div>
                    <div class="mode-title">从左边选一篇，按 3 步走就行</div>
                    <p>1. 先点“打开链接”拿全文。2. 在右侧标记“已获取 / 无权限 / 暂缓”。3. 全文看完后，再决定纳入报告还是最终排除。</p>
                    <div class="summary-strip">
                      <div class="summary-box"><span>待获取全文</span><strong>{{ workbenchSummary.needs_link + workbenchSummary.needs_access }}</strong></div>
                      <div class="summary-box"><span>待终判</span><strong>{{ workbenchSummary.ready_for_decision }}</strong></div>
                      <div class="summary-box"><span>已纳入报告</span><strong>{{ workbenchSummary.report_included }}</strong></div>
                    </div>
                  </div>
                </NCard>
              </div>
            </section>
          </NTabPane>

          <NTabPane name="rounds" tab="轮次复核">
            <section class="workspace-grid">
              <NCard class="panel-surface records-card" embedded>
                <div class="card-title-row">
                  <div>
                    <div class="section-title">轮次级筛选纠偏</div>
                    <div class="section-copy">这里只处理当前轮次的改判。</div>
                  </div>
                  <div class="section-meta">{{ selectedRoundTaskLabel }}</div>
                </div>
                <NForm label-placement="top">
                  <NFormItem label="筛选轮次">
                    <NSelect v-model:value="selectedScreeningTaskId" :options="roundTaskOptions" placeholder="选择需要复核的筛选轮次" />
                  </NFormItem>
                </NForm>
                <div class="summary-strip">
                  <div class="summary-box"><span>纳入</span><strong>{{ selectedRoundSummary.included }}</strong></div>
                  <div class="summary-box"><span>剔除</span><strong>{{ selectedRoundSummary.excluded }}</strong></div>
                  <div class="summary-box"><span>不确定</span><strong>{{ selectedRoundSummary.uncertain }}</strong></div>
                  <div class="summary-box"><span>已处理</span><strong>{{ selectedRoundSummary.processed }}</strong></div>
                </div>

                <div class="records-toolbar">
                  <NInput v-model:value="roundSearch" placeholder="按标题、期刊、DOI 或理由搜索本轮记录">
                    <template #prefix><Search :size="16" /></template>
                  </NInput>
                  <NSelect
                    v-model:value="roundDecisionFilter"
                    :options="[
                      { label: '全部结论', value: 'all' },
                      { label: '纳入', value: 'include' },
                      { label: '剔除', value: 'exclude' },
                      { label: '不确定', value: 'uncertain' }
                    ]"
                  />
                </div>

                <NSpin :show="loadingScreeningTask">
                  <div v-if="filteredRoundRows.length" class="record-list">
                    <article
                      v-for="row in filteredRoundRows"
                      :key="row.paper_id"
                      class="record-row"
                      :class="{ active: activeRoundPaperId === row.paper_id }"
                      @click="setActiveRoundRow(row.paper_id)"
                    >
                      <div class="record-check">
                        <NCheckbox
                          :checked="selectedRoundIdSet.has(row.paper_id)"
                          @click.stop
                          @update:checked="(checked) => toggleRoundRowSelected(row.paper_id, checked)"
                        />
                      </div>
                      <div class="record-main">
                        <div class="record-head">
                          <h2>{{ row.title }}</h2>
                          <div class="record-tags">
                            <NTag round size="small" :type="screeningDecisionType(row.decision)">{{ screeningDecisionLabel(row.decision) }}</NTag>
                            <NTag round size="small">{{ row.year ?? '----' }}</NTag>
                          </div>
                        </div>
                        <div class="record-meta">{{ row.journal || '未知期刊' }}</div>
                        <div class="record-reason">{{ row.reason }}</div>
                      </div>
                    </article>
                  </div>
                  <NEmpty v-else class="empty-state" :description="screeningTaskDetail ? '当前轮次在这个筛选条件下没有匹配记录' : '当前线程还没有可复核的筛选轮次'" />
                </NSpin>
              </NCard>

              <div class="inspector-stack">
                <NCard class="panel-surface inspector-card" embedded>
                  <template v-if="activeRoundRow">
                    <div class="card-title-row">
                      <div>
                        <div class="section-title">单篇改判</div>
                        <div class="section-copy">保存后会自动刷新候选池。</div>
                      </div>
                    </div>
                    <div class="record-focus-title">{{ activeRoundRow.title }}</div>
                    <div class="focus-meta">
                      <span>{{ activeRoundRow.year || '年份未知' }}</span>
                      <span>{{ activeRoundRow.journal || '期刊未知' }}</span>
                    </div>
                    <div class="abstract-block">
                      <div class="abstract-label">摘要</div>
                      <div class="abstract-panel">{{ activeRoundRow.abstract || '当前记录没有可用摘要。' }}</div>
                    </div>
                    <NForm label-placement="top">
                      <NFormItem label="筛选判定">
                        <NSelect
                          v-model:value="activeRoundDecision"
                          :options="[
                            { label: '纳入', value: 'include' },
                            { label: '剔除', value: 'exclude' },
                            { label: '不确定', value: 'uncertain' }
                          ]"
                        />
                      </NFormItem>
                      <NFormItem label="复核理由">
                        <NInput v-model:value="activeRoundReason" type="textarea" :autosize="{ minRows: 4, maxRows: 8 }" />
                      </NFormItem>
                    </NForm>
                    <NButton type="primary" :loading="screeningSubmitting" @click="saveActiveRoundReview">保存本轮改判</NButton>
                  </template>
                  <div v-else class="empty-inspector">
                    <div class="mode-title">还没有选中本轮记录</div>
                    <p>点左侧任意一条记录进入单篇改判，或者在下方直接用批量匹配处理标题 / 参考文献列表。</p>
                  </div>
                </NCard>

                <NCard class="panel-surface inspector-card" embedded>
                  <div class="card-title-row">
                    <div>
                      <div class="section-title">批量改判</div>
                      <div class="section-copy">支持批量改判和自动匹配。</div>
                    </div>
                    <div class="section-meta">已勾选 {{ selectedRoundPaperIds.length }} 篇</div>
                  </div>
                  <NForm label-placement="top">
                    <NFormItem label="批量判定结果">
                      <NSelect
                        v-model:value="batchRoundDecision"
                        :options="[
                          { label: '纳入', value: 'include' },
                          { label: '剔除', value: 'exclude' },
                          { label: '不确定', value: 'uncertain' }
                        ]"
                      />
                    </NFormItem>
                    <NFormItem label="批量审核理由">
                      <NInput v-model:value="batchRoundReason" />
                    </NFormItem>
                  </NForm>
                  <div class="action-grid">
                    <NButton type="primary" secondary :disabled="!selectedRoundPaperIds.length" :loading="screeningSubmitting" @click="saveSelectedRoundReview">
                      对勾选记录批量改判
                    </NButton>
                  </div>
                  <NDivider />
                  <NForm label-placement="top">
                    <NFormItem label="标题或参考文献列表">
                      <NInput
                        v-model:value="bulkReviewText"
                        type="textarea"
                        :autosize="{ minRows: 6, maxRows: 12 }"
                        placeholder="支持整段参考文献列表，或一行一个标题"
                      />
                    </NFormItem>
                  </NForm>
                  <NButton type="primary" :loading="screeningSubmitting" :disabled="!bulkReviewText.trim()" @click="submitBulkRoundReview">
                    一键批量应用
                  </NButton>
                </NCard>
              </div>
            </section>
          </NTabPane>
        </NTabs>
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

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) minmax(360px, 0.82fr);
  gap: 16px;
  align-items: start;
}

.candidate-main-stack,
.inspector-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-title-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
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
  white-space: nowrap;
}

.focus-board {
  background:
    linear-gradient(180deg, rgba(255, 252, 245, 0.92), rgba(248, 244, 233, 0.92));
  border: 1px solid rgba(129, 120, 92, 0.1);
}

.workflow-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
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

.summary-chip {
  border: 1px solid rgba(125, 117, 98, 0.16);
  background: rgba(255, 255, 255, 0.8);
  border-radius: 999px;
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.summary-chip.active {
  background: #172d13;
  color: #fff;
  border-color: #172d13;
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
.records-toolbar,
.action-grid,
.link-actions,
.filter-actions,
.selection-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.records-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(220px, 0.5fr);
  gap: 12px;
}

.compact-toolbar {
  margin-bottom: 12px;
}

.filter-actions {
  margin-bottom: 14px;
}

.filter-drawer {
  margin-bottom: 14px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(247, 244, 236, 0.92);
  border: 1px solid rgba(125, 117, 98, 0.12);
}

.drawer-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.drawer-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 6px;
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

.record-quick-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
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

@media (max-width: 1100px) {
  .workspace-grid,
  .review-hero {
    flex-direction: column;
  }

  .records-toolbar,
  .drawer-grid,
  .workflow-cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .card-title-row,
  .step-head,
  .record-head {
    flex-direction: column;
  }

  .record-row,
  .step-card {
    grid-template-columns: 1fr;
  }

  .step-index {
    width: 36px;
    height: 36px;
    border-radius: 12px;
  }
}
</style>
