<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { BookOpenText, FileSearch, FileText, Pencil, RefreshCw, Sparkles, Trash2, Wand2 } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NDynamicInput,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NSelect,
  NSpace,
  NTag,
  useMessage
} from 'naive-ui'
import ThreadMessageCard from '@/components/ThreadMessageCard.vue'
import { fetchProviderModels, getArtifactUrl, prefillThreadSetup } from '@/api/client'
import { useDraftsStore } from '@/stores/drafts'
import { useMetaStore } from '@/stores/meta'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import { buildCriteriaMarkdown } from '@/utils/strategy'
import type { DatasetRecord, ProviderName, StrategyDatabase, TaskSnapshot, ThreadProfile } from '@/types/api'
import type { ThreadAction, ThreadMessage, ThreadMetric } from '@/types/thread'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const projectsStore = useProjectsStore()
const tasksStore = useTasksStore()
const metaStore = useMetaStore()
const draftsStore = useDraftsStore()

const projectId = computed(() => String(route.params.projectId))
const project = computed(() => projectsStore.currentProject)
const threadProfile = computed<ThreadProfile | null>(() => project.value?.thread_profile ?? null)

const reportTitle = ref('')
const reportTopic = ref('')
const reportName = ref('simple_report')
const reportReferenceStyle = ref<'gbt7714' | 'apa7'>('gbt7714')
const reportModelForm = ref({
  provider: 'deepseek' as ProviderName,
  modelName: 'deepseek-reasoner',
  apiBaseUrl: 'https://api.deepseek.com/v1',
  apiKeyEnv: 'DEEPSEEK_API_KEY',
  apiKey: ''
})
const selectedReportDatasetIds = ref<string[]>([])
const reportModelOptions = ref<Array<{ label: string; value: string }>>([])
const reportModelsLoading = ref(false)
const reportModelFetchError = ref('')
const editingThread = ref(false)
const assistingThread = ref(false)
const assistSubmitting = ref(false)
const editForm = ref({
  name: '',
  description: '',
  researchNeed: '',
  topic: '',
  inclusion: [''],
  exclusion: [''],
  selectedDatabases: ['scopus', 'wos', 'pubmed', 'cnki'] as StrategyDatabase[]
})
const assistForm = ref({
  selectedDatabases: ['scopus', 'wos', 'pubmed', 'cnki'] as StrategyDatabase[],
  provider: 'deepseek' as ProviderName,
  modelName: 'deepseek-reasoner',
  apiBaseUrl: 'https://api.deepseek.com/v1',
  apiKeyEnv: 'DEEPSEEK_API_KEY',
  apiKey: '',
  timeoutSeconds: 180
})
const pollTimer = ref<number | null>(null)
const reportPanelRef = ref<HTMLElement | null>(null)
const reportFocusNote = ref('')
const reportPanelHighlighted = ref(false)
let reportFocusTimer: number | null = null
let reportModelRequestToken = 0
let reportModelReloadTimer: number | null = null

const datasetMap = computed(() => {
  const map = new Map<string, DatasetRecord>()
  for (const dataset of project.value?.datasets ?? []) {
    map.set(dataset.id, dataset)
  }
  return map
})

const tasks = computed(() => [...(project.value?.tasks ?? [])].sort((a, b) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf()))
const taskMap = computed(() => {
  const map = new Map<string, TaskSnapshot>()
  for (const task of tasks.value) {
    map.set(task.id, task)
  }
  return map
})
const screeningRounds = computed(() => tasks.value.filter((task) => task.kind === 'screening'))

const screeningDefaults = computed(() => threadProfile.value?.screening ?? null)
const strategyContext = computed(() => threadProfile.value?.strategy ?? null)
const reportDraftKey = computed(() => project.value?.id ?? null)
const reportSourceDataset = computed(() =>
  (project.value?.datasets ?? []).find((dataset) => dataset.kind === 'fulltext_ready')
  ?? null
)
const reportSourceDatasets = computed(() =>
  (project.value?.datasets ?? []).filter((dataset) =>
    ['fulltext_ready', 'included_reviewed', 'included', 'cumulative_included'].includes(dataset.kind)
  )
)
const reportSourceOptions = computed(() =>
  reportSourceDatasets.value.map((dataset) => ({
    label: reportDatasetOptionLabel(dataset),
    value: dataset.id,
    disabled: (dataset.record_count ?? 0) <= 0
  }))
)
const selectedReportDatasets = computed(() =>
  selectedReportDatasetIds.value
    .map((datasetId) => datasetMap.value.get(datasetId) ?? null)
    .filter((dataset): dataset is DatasetRecord => Boolean(dataset))
)
const selectedReportSourceCount = computed(() =>
  selectedReportDatasets.value.reduce((total, dataset) => total + Number(dataset.record_count ?? 0), 0)
)
const fulltextReadyCount = computed(() =>
  (project.value?.datasets ?? []).find((dataset) => dataset.kind === 'fulltext_ready')?.record_count ?? 0
)

const workbenchSummary = computed(() => project.value?.workbench.summary ?? {
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

const stageCards = computed(() => [
  {
    title: '线程方案',
    description: strategyContext.value?.plan ? '已生成' : '待生成',
    value: strategyContext.value?.plan ? strategyContext.value.selected_databases.length : 0,
    unit: '个数据库',
    emphasis: strategyContext.value?.plan ? 'ready' : 'pending'
  },
  {
    title: '初筛轮次',
    description: screeningRounds.value.length ? '可继续新增筛选轮次或复核结果' : '还没有初筛轮次',
    value: screeningRounds.value.length,
    unit: '轮',
    emphasis: screeningRounds.value.length ? 'ready' : 'pending'
  },
  {
    title: '复核与全文',
    description: workbenchSummary.value.total_candidates ? '在这里复核文献并标记全文获取状态' : '初筛完成后候选文献会进入这里',
    value: workbenchSummary.value.actionable_candidates,
    unit: '篇候选',
    emphasis: workbenchSummary.value.actionable_candidates ? 'ready' : 'pending'
  },
  {
    title: '报告生成',
    description: fulltextReadyCount.value > 0 ? '可从已获取全文中选择本次输入' : '暂无已获取全文',
    value: fulltextReadyCount.value,
    unit: '篇已获取',
    emphasis: fulltextReadyCount.value > 0 ? 'ready' : 'pending'
  }
])

function latestMatchingDataset(task: TaskSnapshot, kinds: string[]) {
  const matches = task.output_dataset_ids
    .map((datasetId) => datasetMap.value.get(datasetId) ?? null)
    .filter((dataset): dataset is DatasetRecord => Boolean(dataset && kinds.includes(dataset.kind)))
  return matches.length ? matches[matches.length - 1] : null
}

function reportDatasetKindLabel(kind: string) {
  switch (kind) {
    case 'report_source':
      return '旧版报告输入'
    case 'fulltext_ready':
      return '已获取全文'
    case 'included_reviewed':
      return '人工复核后纳入'
    case 'included':
      return '本轮纳入'
    case 'cumulative_included':
      return '累计纳入'
    default:
      return kind
  }
}

function reportDatasetOptionLabel(dataset: DatasetRecord) {
  const taskTitle = dataset.task_id ? taskMap.value.get(dataset.task_id)?.title : ''
  const roundLabel = taskTitle ? ` · ${taskTitle}` : ''
  return `${reportDatasetKindLabel(dataset.kind)}${roundLabel} · ${dataset.record_count ?? 0} 篇`
}

function defaultReportDatasetIds(draftDatasetIds: string[] = []) {
  const validOptions = new Set(reportSourceOptions.value.filter((option) => !option.disabled).map((option) => option.value))
  const fromDraft = [...new Set(draftDatasetIds)].filter((datasetId) => validOptions.has(datasetId))
  if (fromDraft.length) return fromDraft
  if (reportSourceDataset.value && validOptions.has(reportSourceDataset.value.id)) return [reportSourceDataset.value.id]
  const firstAvailable = reportSourceDatasets.value.find((dataset) => validOptions.has(dataset.id))
  return firstAvailable ? [firstAvailable.id] : []
}

function sourceLabelOf(task: TaskSnapshot) {
  if (task.input_dataset_ids.length) {
    const labels = task.input_dataset_ids
      .map((datasetId) => datasetMap.value.get(datasetId)?.label ?? datasetId)
      .filter(Boolean)
    if (labels.length) return `来源：${labels.join(' + ')}`
  }
  if (task.parent_task_id) return '来源：延续上一轮'
  if (task.kind === 'report') return '输入：本次报告生成所选文献'
  if (task.kind === 'strategy') return '来源：研究需求生成线程方案'
  return '来源：新上传文献'
}

function firstLine(text: string | null | undefined) {
  return (text ?? '').split('\n')[0]?.trim() ?? ''
}

function screeningMetrics(task: TaskSnapshot): ThreadMetric[] {
  const summary = task.summary ?? {}
  const metrics: ThreadMetric[] = []
  if (summary.raw_entries_count !== undefined) metrics.push({ label: '原始', value: Number(summary.raw_entries_count) || 0 })
  if (summary.included_count !== undefined) metrics.push({ label: '纳入', value: Number(summary.included_count) || 0 })
  if (summary.excluded_count !== undefined) metrics.push({ label: '剔除', value: Number(summary.excluded_count) || 0 })
  if (summary.unused_count !== undefined) metrics.push({ label: '未使用', value: Number(summary.unused_count) || 0 })
  return metrics
}

function artifactByKey(task: TaskSnapshot, key: string) {
  return task.artifacts.find((artifact) => artifact.key === key) ?? null
}

function buildStrategyActions(task: TaskSnapshot): ThreadAction[] {
  const actions: ThreadAction[] = [
    { id: `${task.id}-detail`, label: '查看方案详情', kind: 'route', to: `/tasks/${task.id}`, emphasis: 'ghost' }
  ]
  const markdownArtifact = artifactByKey(task, 'strategy_plan')
  if (markdownArtifact) {
    actions.push({
      id: `${task.id}-download-markdown`,
      label: '下载检索方案',
      kind: 'download',
      href: getArtifactUrl(task.id, markdownArtifact.key),
      emphasis: 'ghost'
    })
  }
  actions.push({
    id: `${task.id}-screening`,
    label: '开始新一轮初筛',
    kind: 'route',
    to: `/threads/${projectId.value}/screening/new`,
    emphasis: 'primary'
  })
  return actions
}

function buildScreeningActions(task: TaskSnapshot): ThreadAction[] {
  const actions: ThreadAction[] = [
    { id: `${task.id}-detail`, label: '查看本轮详情', kind: 'route', to: `/tasks/${task.id}`, emphasis: 'ghost' }
  ]
  const unusedDataset = latestMatchingDataset(task, ['unused'])
  if (unusedDataset) {
    actions.push({
      id: `${task.id}-continue-unused`,
      label: '继续筛选未使用文献',
      kind: 'route',
      to: `/threads/${projectId.value}/screening/new?sourceDatasetId=${unusedDataset.id}&parentTaskId=${task.id}`,
      emphasis: 'primary'
    })
  }
  const includedDataset = latestMatchingDataset(task, ['included_reviewed', 'included'])
  if (includedDataset) {
    actions.push({
      id: `${task.id}-fulltext`,
      label: '进入复核与全文工作台',
      kind: 'route',
      to: `/threads/${projectId.value}/fulltext?screeningTaskId=${task.id}`,
      emphasis: 'secondary'
    })
  }
  return actions
}

function buildReportActions(task: TaskSnapshot): ThreadAction[] {
  const actions: ThreadAction[] = [
    { id: `${task.id}-detail`, label: '查看报告详情', kind: 'route', to: `/tasks/${task.id}`, emphasis: 'ghost' }
  ]
  const reportArtifact = artifactByKey(task, 'literature_report')
  if (reportArtifact) {
    actions.push({
      id: `${task.id}-download-report`,
      label: '下载报告',
      kind: 'download',
      href: getArtifactUrl(task.id, reportArtifact.key),
      emphasis: 'primary'
    })
  }
  return actions
}

function buildThreadMessage(task: TaskSnapshot): ThreadMessage {
  if (task.kind === 'strategy') {
    const databaseCount = Number(task.summary?.database_count ?? strategyContext.value?.selected_databases.length ?? 0)
    return {
      id: task.id,
      taskId: task.id,
      kind: task.kind,
      status: task.status,
      title: task.title,
      eyebrow: 'Thread Plan',
      body:
        task.status === 'succeeded'
          ? '线程方案已生成，顶部主题和筛选标准已经更新。'
          : task.status === 'failed'
            ? `线程方案生成失败。${firstLine(task.error) || task.progress_message || '请进入详情页查看错误。'}`
            : task.progress_message || '正在生成线程主题、筛选标准和检索式。',
      sourceLabel: sourceLabelOf(task),
      note: task.status === 'succeeded' ? '后续新筛选轮次会默认继承这套主题与标准。' : undefined,
      createdAt: task.created_at,
      updatedAt: task.updated_at,
      phaseLabel: task.phase_label,
      progressCurrent: task.progress_current,
      progressTotal: task.progress_total,
      progressMessage: task.progress_message,
      metrics: [{ label: '数据库', value: databaseCount }],
      actions: buildStrategyActions(task)
    }
  }

  if (task.kind === 'screening') {
    const summary = task.summary ?? {}
    return {
      id: task.id,
      taskId: task.id,
      kind: task.kind,
      status: task.status,
      title: task.title,
      eyebrow: 'Screening Round',
      body:
        task.status === 'succeeded'
          ? `本轮初筛完成。纳入 ${Number(summary.included_count ?? 0)} 篇，剔除 ${Number(summary.excluded_count ?? 0)} 篇，不确定 ${Number(summary.uncertain_count ?? 0)} 篇。`
          : task.status === 'failed'
            ? `本轮执行失败。${firstLine(task.error) || task.progress_message || '请进入详情页查看错误。'}`
            : task.progress_message || '正在执行这一轮初筛。',
      sourceLabel: sourceLabelOf(task),
      note: task.status === 'succeeded' ? '下一步建议去复核与全文工作台打开链接并标记全文状态。' : undefined,
      createdAt: task.created_at,
      updatedAt: task.updated_at,
      phaseLabel: task.phase_label,
      progressCurrent: task.progress_current,
      progressTotal: task.progress_total,
      progressMessage: task.progress_message,
      metrics: screeningMetrics(task),
      actions: buildScreeningActions(task)
    }
  }

  return {
    id: task.id,
    taskId: task.id,
    kind: task.kind,
    status: task.status,
    title: task.title,
    eyebrow: 'Report Task',
    body:
      task.status === 'succeeded'
        ? '报告已生成。'
        : task.status === 'failed'
          ? `报告生成失败。${firstLine(task.error) || task.progress_message || '请进入详情页查看错误。'}`
          : task.progress_message || '正在生成报告。',
    sourceLabel: sourceLabelOf(task),
    createdAt: task.created_at,
    updatedAt: task.updated_at,
    phaseLabel: task.phase_label,
    progressCurrent: task.progress_current,
    progressTotal: task.progress_total,
    progressMessage: task.progress_message,
    metrics: [{ label: '样式', value: String(task.summary?.reference_style ?? 'gbt7714').toUpperCase() }],
    actions: buildReportActions(task)
  }
}

const threadMessages = computed(() => tasks.value.slice().reverse().map(buildThreadMessage))

function initializeReportDefaults() {
  if (!project.value) return
  const preferredProvider = (threadProfile.value?.strategy.model?.provider ?? metaStore.strategyDefaults.provider) as ProviderName
  const preset = metaStore.providerPresets.find((item) => item.provider === preferredProvider)
  const draft = reportDraftKey.value ? draftsStore.reportDrafts[reportDraftKey.value] ?? null : null
  const nextProvider = (draft?.provider ?? preferredProvider) as ProviderName
  const nextPreset = metaStore.providerPresets.find((item) => item.provider === nextProvider) ?? preset
  reportTitle.value = draft?.title?.trim() || `${project.value.name}-report`
  reportTopic.value = draft?.projectTopic?.trim() || screeningDefaults.value?.topic || project.value.topic
  reportName.value = draft?.reportName?.trim() || 'simple_report'
  reportReferenceStyle.value = draft?.referenceStyle ?? 'gbt7714'
  reportModelForm.value = {
    provider: nextProvider,
    modelName: draft?.modelName?.trim() || threadProfile.value?.strategy.model?.model_name || nextPreset?.defaultModel || metaStore.strategyDefaults.model_name,
    apiBaseUrl: draft?.apiBaseUrl?.trim() || threadProfile.value?.strategy.model?.api_base_url || nextPreset?.defaultBaseUrl || metaStore.strategyDefaults.api_base_url,
    apiKeyEnv: draft?.apiKeyEnv?.trim() || threadProfile.value?.strategy.model?.api_key_env || nextPreset?.defaultApiKeyEnv || metaStore.strategyDefaults.api_key_env,
    apiKey: draftsStore.getProviderApiKey(nextProvider)
  }
  selectedReportDatasetIds.value = defaultReportDatasetIds(draft?.datasetIds ?? [])
  setFallbackReportModelOptions(nextProvider)
  void loadReportModelOptions({ silent: true })
}

function openEditThread() {
  if (!project.value || !threadProfile.value) return
  editForm.value = {
    name: project.value.name,
    description: project.value.description ?? '',
    researchNeed: threadProfile.value.strategy.research_need ?? '',
    topic: threadProfile.value.screening.topic || '',
    inclusion: threadProfile.value.screening.inclusion.length ? [...threadProfile.value.screening.inclusion] : [''],
    exclusion: threadProfile.value.screening.exclusion.length ? [...threadProfile.value.screening.exclusion] : [''],
    selectedDatabases: threadProfile.value.strategy.selected_databases.length
      ? [...threadProfile.value.strategy.selected_databases]
      : ['scopus', 'wos', 'pubmed', 'cnki']
  }
  editingThread.value = true
}

function clearThreadEditorQueryFlag() {
  if (!('editThread' in route.query)) return
  const nextQuery = { ...route.query }
  delete nextQuery.editThread
  void router.replace({ path: route.path, query: nextQuery })
}

function openThreadAssist() {
  const strategyModel = threadProfile.value?.strategy.model
  assistForm.value = {
    selectedDatabases: (
      threadProfile.value?.strategy.selected_databases.length
        ? [...threadProfile.value.strategy.selected_databases]
        : metaStore.strategyDefaults.databases.map((item) => item.value)
    ) as StrategyDatabase[],
    provider: (strategyModel?.provider ?? metaStore.strategyDefaults.provider) as ProviderName,
    modelName: strategyModel?.model_name ?? metaStore.strategyDefaults.model_name,
    apiBaseUrl: strategyModel?.api_base_url ?? metaStore.strategyDefaults.api_base_url,
    apiKeyEnv: strategyModel?.api_key_env ?? metaStore.strategyDefaults.api_key_env,
    apiKey: draftsStore.getProviderApiKey((strategyModel?.provider ?? metaStore.strategyDefaults.provider) as ProviderName),
    timeoutSeconds: 180
  }
  assistingThread.value = true
}

function applyAssistProviderPreset(nextProvider: ProviderName) {
  const preset = metaStore.providerPresets.find((item) => item.provider === nextProvider)
  if (!preset) return
  assistForm.value = {
    ...assistForm.value,
    provider: nextProvider,
    modelName: nextProvider === 'deepseek' ? metaStore.strategyDefaults.model_name : preset.defaultModel,
    apiBaseUrl: preset.defaultBaseUrl,
    apiKeyEnv: preset.defaultApiKeyEnv,
    apiKey: draftsStore.getProviderApiKey(nextProvider)
  }
}

function applyReportProviderPreset(nextProvider: ProviderName) {
  const preset = metaStore.providerPresets.find((item) => item.provider === nextProvider)
  if (!preset) return
  reportModelForm.value = {
    provider: nextProvider,
    modelName: preset.defaultModel,
    apiBaseUrl: preset.defaultBaseUrl,
    apiKeyEnv: preset.defaultApiKeyEnv,
    apiKey: draftsStore.getProviderApiKey(nextProvider)
  }
  setFallbackReportModelOptions(nextProvider)
  void loadReportModelOptions({ silent: true })
}

function fallbackReportModelOptions(nextProvider: ProviderName) {
  if (nextProvider === 'deepseek') {
    return [
      { label: 'deepseek-chat', value: 'deepseek-chat' },
      { label: 'deepseek-reasoner', value: 'deepseek-reasoner' }
    ]
  }
  const preset = metaStore.providerPresets.find((item) => item.provider === nextProvider)
  const modelName = preset?.defaultModel || 'moonshot-v1-auto'
  return [{ label: modelName, value: modelName }]
}

function setFallbackReportModelOptions(nextProvider: ProviderName = reportModelForm.value.provider) {
  reportModelOptions.value = fallbackReportModelOptions(nextProvider)
  if (!reportModelOptions.value.some((option) => option.value === reportModelForm.value.modelName)) {
    reportModelForm.value = {
      ...reportModelForm.value,
      modelName: reportModelOptions.value[0]?.value || reportModelForm.value.modelName
    }
  }
}

async function loadReportModelOptions(options: { silent?: boolean } = {}) {
  const requestToken = ++reportModelRequestToken
  const currentForm = { ...reportModelForm.value }
  reportModelsLoading.value = true
  reportModelFetchError.value = ''
  try {
    const response = await fetchProviderModels({
      provider: currentForm.provider,
      api_base_url: currentForm.apiBaseUrl,
      api_key_env: currentForm.apiKeyEnv,
      api_key: currentForm.apiKey || null
    })
    if (requestToken !== reportModelRequestToken || currentForm.provider !== reportModelForm.value.provider) return
    const providerOptions = response.models.map((item) => ({
      label: item.label || item.id,
      value: item.id
    }))
    reportModelOptions.value = providerOptions.length ? providerOptions : fallbackReportModelOptions(currentForm.provider)
    if (!reportModelOptions.value.some((option) => option.value === reportModelForm.value.modelName)) {
      reportModelForm.value = {
        ...reportModelForm.value,
        modelName: reportModelOptions.value[0]?.value || reportModelForm.value.modelName
      }
    }
    reportModelFetchError.value = response.source === 'fallback' && response.error ? '未能从服务商获取模型，已使用默认模型。' : ''
  } catch {
    if (requestToken !== reportModelRequestToken || currentForm.provider !== reportModelForm.value.provider) return
    setFallbackReportModelOptions(currentForm.provider)
    reportModelFetchError.value = '未能从服务商获取模型，已使用默认模型。'
  } finally {
    if (requestToken === reportModelRequestToken) {
      reportModelsLoading.value = false
    }
  }
  if (!options.silent && reportModelFetchError.value) {
    message.warning(reportModelFetchError.value)
  }
}

function scheduleReportModelReload() {
  if (typeof window === 'undefined') return
  if (reportModelReloadTimer !== null) window.clearTimeout(reportModelReloadTimer)
  reportModelReloadTimer = window.setTimeout(() => {
    reportModelReloadTimer = null
    void loadReportModelOptions({ silent: true })
  }, 700)
}

function updateReportApiKey(value: string) {
  reportModelForm.value.apiKey = value
  draftsStore.setProviderApiKey(reportModelForm.value.provider, value)
  scheduleReportModelReload()
}

async function saveThreadEdits() {
  if (!project.value || !threadProfile.value) return
  const nextTopic = editForm.value.topic.trim() || project.value.topic
  const nextInclusion = editForm.value.inclusion.filter(Boolean)
  const nextExclusion = editForm.value.exclusion.filter(Boolean)
  const updatedProfile: ThreadProfile = {
    ...threadProfile.value,
    strategy: {
      ...threadProfile.value.strategy,
      research_need: editForm.value.researchNeed.trim(),
      selected_databases: editForm.value.selectedDatabases
    },
    screening: {
      ...threadProfile.value.screening,
      topic: nextTopic,
      inclusion: nextInclusion,
      exclusion: nextExclusion,
      criteria_markdown: buildCriteriaMarkdown(nextTopic, nextInclusion, nextExclusion)
    }
  }
  await projectsStore.updateProjectWorkflow(project.value.id, {
    name: editForm.value.name.trim() || project.value.name,
    topic: nextTopic,
    description: editForm.value.description.trim(),
    thread_profile: updatedProfile
  })
  editingThread.value = false
  initializeReportDefaults()
  message.success('线程上下文已更新')
}

async function applyAiThreadAssist() {
  if (!project.value || !threadProfile.value) return
  const researchNeed = threadProfile.value.strategy.research_need?.trim()
  if (!researchNeed) {
    message.warning('这个线程还没有研究需求，先手动补上研究需求，再使用 AI 识别主题与筛选条件。')
    return
  }
  if (!assistForm.value.selectedDatabases.length) {
    message.warning('至少保留一个数据库，AI 才能结合检索场景识别主题与筛选条件。')
    return
  }
  assistSubmitting.value = true
  try {
    const response = await prefillThreadSetup({
      research_need: researchNeed,
      selected_databases: [...assistForm.value.selectedDatabases],
      timeout_seconds: assistForm.value.timeoutSeconds || 180,
      model: {
        provider: assistForm.value.provider,
        model_name: assistForm.value.modelName,
        api_base_url: assistForm.value.apiBaseUrl,
        api_key_env: assistForm.value.apiKeyEnv,
        api_key: assistForm.value.apiKey,
        temperature: 0,
        max_tokens: 4096,
        min_request_interval_seconds: 2
      }
    })
    draftsStore.setProviderApiKey(assistForm.value.provider, assistForm.value.apiKey)
    const nextTopic = response.strategy_plan.screening_topic || response.strategy_plan.topic || project.value.topic
    const nextDescription = project.value.description?.trim() || response.strategy_plan.intent_summary
    await projectsStore.updateProjectWorkflow(project.value.id, {
      name: project.value.name,
      topic: nextTopic,
      description: nextDescription,
      thread_profile: {
        ...threadProfile.value,
        strategy: {
          ...threadProfile.value.strategy,
          selected_databases: [...assistForm.value.selectedDatabases],
          model: {
            provider: assistForm.value.provider,
            model_name: assistForm.value.modelName,
            api_base_url: assistForm.value.apiBaseUrl,
            api_key_env: assistForm.value.apiKeyEnv,
            temperature: 0,
            max_tokens: 4096,
            min_request_interval_seconds: 2
          }
        },
        screening: {
          ...threadProfile.value.screening,
          topic: nextTopic,
          inclusion: [...response.strategy_plan.inclusion],
          exclusion: [...response.strategy_plan.exclusion],
          criteria_markdown: response.criteria_markdown
        }
      }
    })
    assistingThread.value = false
    initializeReportDefaults()
    message.success('AI 已经把主题与筛选条件写回当前线程')
  } catch (error) {
    const detail = (error as { response?: { data?: { detail?: unknown } } } | null)?.response?.data?.detail
    message.error(typeof detail === 'string' && detail ? detail : 'AI 识别主题与筛选条件失败')
  } finally {
    assistSubmitting.value = false
  }
}

async function removeCurrentThread() {
  if (!project.value) return
  if (!window.confirm(`确认删除主题“${project.value.name}”？相关初筛和报告生成任务也会一起删除。`)) {
    return
  }
  stopProjectPolling()
  await projectsStore.deleteProject(project.value.id)
  await tasksStore.refreshList()
  editingThread.value = false
  message.success('主题线程已删除')
  await router.push('/')
}

watch(projectId, async (nextProjectId) => {
  if (!nextProjectId) return
  await tasksStore.refreshList()
  await projectsStore.loadProject(nextProjectId)
  initializeReportDefaults()
}, { immediate: true })

watch(
  [project, threadProfile, () => route.query.editThread],
  ([currentProject, currentProfile, editThreadQuery]) => {
    if (!currentProject || !currentProfile || !editThreadQuery || editingThread.value) return
    openEditThread()
    clearThreadEditorQueryFlag()
  },
  { immediate: true }
)

watch(
  [() => route.query.reportDatasetId, () => route.query.focusPanel, () => project.value?.id, () => reportSourceOptions.value.length],
  async ([datasetId, focusPanel]) => {
    if (focusPanel !== 'report') {
      reportFocusNote.value = ''
      reportPanelHighlighted.value = false
      return
    }
    const focusedDataset = typeof datasetId === 'string' ? datasetMap.value.get(datasetId) : null
    if (focusedDataset && reportSourceOptions.value.some((option) => option.value === focusedDataset.id && !option.disabled)) {
      selectedReportDatasetIds.value = [focusedDataset.id]
    }
    reportFocusNote.value =
      focusedDataset
        ? '报告输入已经带入，下一步确认报告主题、模型和样式。'
        : '已恢复上一次报告生成参数。确认主题、模型和样式后，可以重新提交。'
    reportPanelHighlighted.value = true
    await nextTick()
    reportPanelRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    if (typeof window !== 'undefined') {
      if (reportFocusTimer !== null) window.clearTimeout(reportFocusTimer)
      reportFocusTimer = window.setTimeout(() => {
        reportPanelHighlighted.value = false
      }, 2600)
    }
  },
  { immediate: true, deep: true }
)

watch(
  [
    reportTitle,
    reportTopic,
    reportName,
    reportReferenceStyle,
    selectedReportDatasetIds,
    () => reportModelForm.value.provider,
    () => reportModelForm.value.modelName,
    () => reportModelForm.value.apiBaseUrl,
    () => reportModelForm.value.apiKeyEnv,
  ],
  () => {
    if (!reportDraftKey.value) return
    draftsStore.updateReportDraft(reportDraftKey.value, {
      projectId: project.value?.id ?? null,
      screeningTaskId: null,
      datasetIds: [...selectedReportDatasetIds.value],
      title: reportTitle.value,
      projectTopic: reportTopic.value,
      reportName: reportName.value,
      referenceStyle: reportReferenceStyle.value,
      provider: reportModelForm.value.provider,
      modelName: reportModelForm.value.modelName,
      apiBaseUrl: reportModelForm.value.apiBaseUrl,
      apiKeyEnv: reportModelForm.value.apiKeyEnv,
    })
  }
)

async function focusReportPanel(note = '确认报告主题、样式和模型后，就可以开始生成报告。') {
  reportFocusNote.value = note
  reportPanelHighlighted.value = true
  await nextTick()
  reportPanelRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  if (typeof window !== 'undefined') {
    if (reportFocusTimer !== null) window.clearTimeout(reportFocusTimer)
    reportFocusTimer = window.setTimeout(() => {
      reportPanelHighlighted.value = false
    }, 2600)
  }
}

function reportMaxTokens(modelName: string) {
  return modelName.trim() === 'deepseek-reasoner' ? 4096 : 1536
}

async function submitThreadReport() {
  if (!project.value) return
  const sourceDatasetIds = [...selectedReportDatasetIds.value]
  if (!sourceDatasetIds.length || selectedReportSourceCount.value <= 0) {
    message.warning('当前纳入文献为 0，无法生成报告。')
    await focusReportPanel('当前选中的报告输入为 0。可以去复核与全文工作台标记已获取全文，或在这里选择某一轮已获取全文批次。')
    return
  }
  draftsStore.setProviderApiKey(reportModelForm.value.provider, reportModelForm.value.apiKey)
  const task = await tasksStore.submitReport({
    title: reportTitle.value.trim() || `${project.value.name}-report`,
    project_id: project.value.id,
    screening_task_id: null,
    dataset_ids: sourceDatasetIds,
    project_topic: reportTopic.value.trim() || screeningDefaults.value?.topic || project.value.topic,
    report_name: reportName.value.trim() || 'simple_report',
    retry_times: 6,
    timeout_seconds: 240,
    reference_style: reportReferenceStyle.value,
    model: {
      provider: reportModelForm.value.provider,
      model_name: reportModelForm.value.modelName.trim() || metaStore.strategyDefaults.model_name,
      api_base_url: reportModelForm.value.apiBaseUrl,
      api_key_env: reportModelForm.value.apiKeyEnv,
      api_key: reportModelForm.value.apiKey,
      temperature: 0,
      max_tokens: reportMaxTokens(reportModelForm.value.modelName),
      min_request_interval_seconds: 2
    }
  })
  if (reportDraftKey.value) {
    draftsStore.clearReportDraft(reportDraftKey.value)
  }
  message.success('报告生成任务已创建')
  await router.push(`/tasks/${task.id}`)
}

function startProjectPolling() {
  if (typeof window === 'undefined' || pollTimer.value !== null) return
  pollTimer.value = window.setInterval(async () => {
    if (!project.value) return
    await Promise.all([tasksStore.refreshList(), projectsStore.loadProject(project.value.id)])
  }, 4000)
}

function stopProjectPolling() {
  if (pollTimer.value !== null && typeof window !== 'undefined') {
    window.clearInterval(pollTimer.value)
  }
  pollTimer.value = null
}

watch(
  () => tasks.value.some((task) => task.status === 'running' || task.status === 'pending'),
  (hasRunning) => {
    if (hasRunning) startProjectPolling()
    else stopProjectPolling()
  },
  { immediate: true }
)

onMounted(async () => {
  draftsStore.hydrate()
  await Promise.all([metaStore.ensureLoaded(), tasksStore.refreshList(), projectsStore.loadProject(projectId.value)])
  initializeReportDefaults()
})

onUnmounted(() => {
  stopProjectPolling()
  if (reportFocusTimer !== null && typeof window !== 'undefined') {
    window.clearTimeout(reportFocusTimer)
  }
  if (reportModelReloadTimer !== null && typeof window !== 'undefined') {
    window.clearTimeout(reportModelReloadTimer)
  }
})
</script>

<template>
  <div v-if="project" class="thread-view">
    <section class="thread-brief panel-surface">
      <div class="thread-brief-head">
        <div>
          <div class="eyebrow">Thread Context</div>
          <h1>{{ project.name }}</h1>
          <p>{{ project.description || '在线程里继续维护主题、标准和进度。' }}</p>
        </div>
        <NSpace>
          <NButton tertiary @click="openEditThread">
            <template #icon><Pencil :size="16" /></template>
            编辑线程信息
          </NButton>
        </NSpace>
      </div>

      <div class="thread-brief-grid">
        <div class="brief-block">
          <div class="brief-label">研究需求</div>
          <div class="brief-value">{{ strategyContext?.research_need || '尚未记录研究需求' }}</div>
        </div>
        <div class="brief-block">
          <div class="brief-label">当前主题</div>
          <div class="brief-value">
            {{ screeningDefaults?.topic || `尚未固定主题（当前先用线程标题占位：${project.topic}）` }}
          </div>
        </div>
        <div class="brief-block">
          <div class="brief-label">纳入标准</div>
          <ul class="brief-list">
            <li v-for="item in screeningDefaults?.inclusion ?? []" :key="item">{{ item }}</li>
            <li v-if="!(screeningDefaults?.inclusion?.length)">尚未生成</li>
          </ul>
        </div>
        <div class="brief-block">
          <div class="brief-label">排除标准</div>
          <ul class="brief-list">
            <li v-for="item in screeningDefaults?.exclusion ?? []" :key="item">{{ item }}</li>
            <li v-if="!(screeningDefaults?.exclusion?.length)">尚未生成</li>
          </ul>
        </div>
      </div>

      <div class="thread-brief-footer">
        <div class="brief-tags">
          <NTag v-for="database in strategyContext?.selected_databases ?? []" :key="database" round>{{ database }}</NTag>
          <NTag round type="success">初筛 {{ screeningRounds.length }} 轮</NTag>
          <NTag round type="warning">候选文献 {{ workbenchSummary.actionable_candidates }} 篇</NTag>
        </div>
        <NSpace>
          <RouterLink :to="`/threads/${project.id}/plan/new`">
            <NButton tertiary>
              <template #icon><Sparkles :size="16" /></template>
              生成检索方案
            </NButton>
          </RouterLink>
          <RouterLink :to="`/threads/${project.id}/screening/new`">
            <NButton type="primary">
              <template #icon><FileSearch :size="16" /></template>
              开始新一轮初筛
            </NButton>
          </RouterLink>
          <RouterLink :to="`/threads/${project.id}/fulltext`">
              <NButton secondary>
                <template #icon><BookOpenText :size="16" /></template>
              进入复核与全文工作台
              </NButton>
            </RouterLink>
          <NButton tertiary type="warning" @click="focusReportPanel()">
            <template #icon><FileText :size="16" /></template>
            生成报告
          </NButton>
        </NSpace>
      </div>
    </section>

    <section class="stage-grid">
      <div v-for="stage in stageCards" :key="stage.title" class="stage-card panel-surface" :class="`stage-${stage.emphasis}`">
        <div class="stage-title">{{ stage.title }}</div>
        <div class="stage-value">{{ stage.value }}<span>{{ stage.unit }}</span></div>
        <div class="stage-copy">{{ stage.description }}</div>
      </div>
    </section>

    <div class="thread-layout">
      <section class="thread-main">
        <NCard title="阶段 1：线程方案" class="panel-surface">
          <template v-if="strategyContext?.plan">
            <div class="section-stack">
              <NAlert type="info" :show-icon="false">
                这里显示当前检索方案。
              </NAlert>
              <div class="strategy-summary">
                <div class="summary-block">
                  <div class="brief-label">需求概括</div>
                  <div class="brief-value">{{ strategyContext.plan.intent_summary }}</div>
                </div>
                <div class="summary-block">
                  <div class="brief-label">线程主题</div>
                  <div class="brief-value">{{ strategyContext.plan.screening_topic }}</div>
                </div>
              </div>
              <div class="search-blocks">
                <div v-for="block in strategyContext.plan.search_blocks" :key="block.database" class="search-block">
                  <div class="search-block-head">{{ block.title }}</div>
                  <pre v-if="block.query" class="search-code">{{ block.query }}</pre>
                  <ul v-else class="brief-list">
                    <li v-for="line in block.lines" :key="line">{{ line }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </template>
          <NEmpty v-else description="还没有检索方案" />
        </NCard>

        <NCard title="阶段 2：初筛轮次" class="panel-surface">
          <div v-if="screeningRounds.length" class="message-stack">
            <ThreadMessageCard
              v-for="messageItem in threadMessages.filter((item) => item.kind === 'screening')"
              :key="messageItem.id"
              :message="messageItem"
              :hide-actions="true"
            />
          </div>
          <NEmpty v-else description="还没有初筛轮次" />
        </NCard>

        <NCard title="阶段 3：复核与全文工作台" class="panel-surface">
          <div class="fulltext-summary-card">
            <div class="fulltext-summary-copy">
              在这里复核初筛结果并标记全文获取状态；生成报告时再选择需要的已获取全文批次。
            </div>
            <div class="fulltext-summary">
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext` }">
                <NTag round :bordered="false" class="summary-tag">全部 {{ workbenchSummary.total_candidates }}</NTag>
              </RouterLink>
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext`, query: { workflow: 'needs-retrieval' } }">
                <NTag round :bordered="false" class="summary-tag">待获取 {{ workbenchSummary.needs_link + workbenchSummary.needs_access }}</NTag>
              </RouterLink>
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext`, query: { stage: 'report-included' } }">
                <NTag round type="success" :bordered="false" class="summary-tag">已获取全文 {{ workbenchSummary.report_included }}</NTag>
              </RouterLink>
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext`, query: { stage: 'unavailable' } }">
                <NTag round type="error" :bordered="false" class="summary-tag">无权限 {{ workbenchSummary.unavailable }}</NTag>
              </RouterLink>
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext`, query: { stage: 'deferred' } }">
                <NTag round type="warning" :bordered="false" class="summary-tag">暂缓 {{ workbenchSummary.deferred }}</NTag>
              </RouterLink>
            </div>
          </div>
        </NCard>

        <div ref="reportPanelRef">
          <NCard title="阶段 4：报告生成" class="panel-surface report-workspace-card" :class="{ highlighted: reportPanelHighlighted }">
            <NAlert v-if="reportFocusNote" type="warning" :show-icon="false" class="report-workspace-alert">
              {{ reportFocusNote }}
            </NAlert>
            <div class="report-workspace-copy">
              基于本次选中的已获取全文批次生成。
            </div>
            <div class="report-workspace-status">
              <NTag round :type="selectedReportSourceCount > 0 ? 'success' : 'warning'">
                已选 {{ selectedReportSourceCount }} 篇
              </NTag>
            </div>
            <NAlert v-if="selectedReportSourceCount <= 0" type="info" :show-icon="false">
              当前选中输入为 0。
            </NAlert>
            <NForm label-placement="top" class="report-form">
              <NFormItem label="报告输入">
                <NSelect
                  v-model:value="selectedReportDatasetIds"
                  multiple
                  clearable
                  :options="reportSourceOptions"
                  placeholder="选择已获取全文批次，必要时也可选择历史纳入数据"
                />
              </NFormItem>
              <NFormItem label="报告生成任务名称">
                <NInput v-model:value="reportTitle" placeholder="例如：某主题文献整理报告" />
              </NFormItem>
              <NFormItem label="报告主题">
                <NInput v-model:value="reportTopic" type="textarea" :autosize="{ minRows: 3, maxRows: 5 }" />
              </NFormItem>
              <div class="report-model-grid">
                <NFormItem label="模型提供商">
                  <NSelect
                    v-model:value="reportModelForm.provider"
                    :options="metaStore.providerPresets.map((item) => ({ label: item.label, value: item.provider }))"
                    @update:value="(value) => applyReportProviderPreset(value as ProviderName)"
                  />
                </NFormItem>
                <NFormItem label="模型名称">
                  <div class="model-select-row">
                    <NSelect
                      v-model:value="reportModelForm.modelName"
                      filterable
                      :loading="reportModelsLoading"
                      :options="reportModelOptions"
                    />
                    <NButton tertiary :loading="reportModelsLoading" @click="loadReportModelOptions()">
                      <template #icon><RefreshCw :size="16" /></template>
                    </NButton>
                  </div>
                  <div v-if="reportModelFetchError" class="field-hint">{{ reportModelFetchError }}</div>
                </NFormItem>
              </div>
              <NFormItem label="API Key">
                <NInput
                  type="password"
                  show-password-on="click"
                  :value="reportModelForm.apiKey"
                  @update:value="updateReportApiKey"
                  @blur="loadReportModelOptions({ silent: true })"
                  placeholder="仅保存在当前浏览器本地"
                />
              </NFormItem>
              <div class="report-model-grid">
                <NFormItem label="参考样式">
                  <NSelect
                    v-model:value="reportReferenceStyle"
                    :options="metaStore.referenceStyles.map((item) => ({ label: item.label, value: item.value }))"
                  />
                </NFormItem>
                <NFormItem label="输出目录名">
                  <NInput v-model:value="reportName" placeholder="simple_report" />
                </NFormItem>
              </div>
            </NForm>
            <NButton type="primary" block @click="submitThreadReport">
              <template #icon><FileText :size="16" /></template>
              基于选中文献生成报告
            </NButton>
          </NCard>
        </div>
      </section>

      <aside class="thread-side">
        <NCard title="活动记录" class="panel-surface">
          <div v-if="threadMessages.length" class="message-stack compact-stack">
            <ThreadMessageCard v-for="messageItem in threadMessages" :key="messageItem.id" :message="messageItem" />
          </div>
          <NEmpty v-else description="线程还没有任何活动记录" />
        </NCard>
      </aside>
    </div>

    <NModal
      :show="editingThread"
      preset="card"
      style="max-width: 880px"
      title="编辑线程信息"
      @update:show="(value) => { editingThread = value }"
    >
      <NForm label-placement="top">
        <NFormItem label="线程名称">
          <NInput v-model:value="editForm.name" />
        </NFormItem>
        <NFormItem label="线程备注">
          <NInput v-model:value="editForm.description" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" />
        </NFormItem>
        <NFormItem label="研究需求">
          <NInput v-model:value="editForm.researchNeed" type="textarea" :autosize="{ minRows: 4, maxRows: 7 }" />
        </NFormItem>
        <NFormItem label="默认主题">
          <NInput v-model:value="editForm.topic" />
        </NFormItem>
        <NFormItem label="默认纳入标准">
          <NDynamicInput v-model:value="editForm.inclusion" :min="1" />
        </NFormItem>
        <NFormItem label="默认排除标准">
          <NDynamicInput v-model:value="editForm.exclusion" :min="1" />
        </NFormItem>
        <NFormItem label="需要保留的数据库检索式">
          <NSelect
            v-model:value="editForm.selectedDatabases"
            multiple
            :options="metaStore.strategyDefaults.databases.map((item) => ({ label: item.label, value: item.value }))"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="space-between">
          <NButton type="error" tertiary @click="removeCurrentThread">
            <template #icon><Trash2 :size="16" /></template>
            删除线程
          </NButton>
          <NSpace>
            <NButton tertiary @click="editingThread = false; openThreadAssist()">
              <template #icon><Wand2 :size="16" /></template>
              AI 识别填入
            </NButton>
            <NButton @click="editingThread = false">取消</NButton>
            <NButton type="primary" @click="saveThreadEdits">保存线程上下文</NButton>
          </NSpace>
        </NSpace>
      </template>
    </NModal>

    <NModal
      :show="assistingThread"
      preset="card"
      style="max-width: 760px"
      title="AI 识别主题与筛选条件"
      @update:show="(value) => { assistingThread = value }"
    >
      <NAlert type="info" :show-icon="false" class="assist-alert">
        根据研究需求识别主题与标准，并写回当前线程。
      </NAlert>
      <NForm label-placement="top">
        <NFormItem label="当前研究需求">
          <NInput :value="strategyContext?.research_need || ''" type="textarea" :autosize="{ minRows: 4, maxRows: 7 }" readonly />
        </NFormItem>
        <NFormItem label="模型提供商">
          <NSelect
            v-model:value="assistForm.provider"
            :options="metaStore.providerPresets.map((item) => ({ label: item.label, value: item.provider }))"
            @update:value="(value) => applyAssistProviderPreset(value as ProviderName)"
          />
        </NFormItem>
        <NFormItem label="模型名称">
          <NInput v-model:value="assistForm.modelName" />
        </NFormItem>
        <NFormItem label="API Key">
          <NInput
            type="password"
            show-password-on="click"
            v-model:value="assistForm.apiKey"
            placeholder="仅保存在当前浏览器本地"
          />
        </NFormItem>
        <NFormItem label="超时时间（秒）">
          <NInputNumber v-model:value="assistForm.timeoutSeconds" :min="30" :max="600" />
        </NFormItem>
        <NFormItem label="数据库范围">
          <NSelect
            v-model:value="assistForm.selectedDatabases"
            multiple
            :options="metaStore.strategyDefaults.databases.map((item) => ({ label: item.label, value: item.value }))"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="assistingThread = false">取消</NButton>
          <NButton type="primary" :loading="assistSubmitting" @click="applyAiThreadAssist">识别并写回线程</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>

  <NEmpty v-else description="线程不存在或仍在加载中" class="panel-surface empty-thread" />
</template>

<style scoped>
.thread-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.thread-brief {
  position: sticky;
  top: 28px;
  z-index: 5;
  padding: 22px 24px;
}

.thread-brief-head {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.thread-brief-head h1 {
  margin: 8px 0;
}

.thread-brief-head p,
.stage-copy,
.fulltext-summary-copy,
.report-workspace-copy {
  color: #5b665d;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 12px;
  color: #6a776c;
}

.thread-brief-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.brief-block {
  padding: 14px;
  border-radius: 16px;
  background: rgba(247, 249, 246, 0.94);
  border: 1px solid rgba(71, 95, 76, 0.12);
}

.brief-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #708074;
  margin-bottom: 8px;
}

.brief-value {
  white-space: pre-wrap;
  line-height: 1.65;
}

.brief-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.7;
}

.thread-brief-footer {
  margin-top: 18px;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
}

.brief-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stage-grid {
  display: grid;
  gap: 16px;
}

.stage-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.stage-card {
  padding: 18px;
}

.stage-title {
  font-weight: 700;
}

.stage-value {
  font-size: 30px;
  font-weight: 700;
  margin: 10px 0 6px;
}

.stage-value span {
  font-size: 14px;
  font-weight: 500;
  margin-left: 6px;
}

.stage-ready {
  background: linear-gradient(135deg, rgba(230, 242, 234, 0.96), rgba(244, 248, 241, 0.96));
}

.stage-pending {
  background: linear-gradient(135deg, rgba(248, 246, 239, 0.96), rgba(247, 249, 246, 0.96));
}

.thread-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr);
  gap: 18px;
  align-items: start;
}

.thread-main,
.thread-side,
.section-stack,
.message-stack,
.search-blocks,
.report-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.compact-stack :deep(.thread-message) {
  margin-bottom: 0;
}

.strategy-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.summary-block {
  padding: 14px;
  border-radius: 16px;
  background: rgba(247, 249, 246, 0.94);
}

.search-block {
  padding: 14px;
  border-radius: 14px;
  background: rgba(241, 245, 240, 0.75);
  border: 1px solid rgba(86, 112, 92, 0.12);
}

.search-block-head {
  font-weight: 700;
  margin-bottom: 8px;
}

.search-code {
  margin: 0;
  white-space: pre-wrap;
  font-family: Consolas, monospace;
  font-size: 13px;
  line-height: 1.65;
}

.fulltext-summary-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.fulltext-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.summary-tag {
  cursor: pointer;
}

.report-workspace-card.highlighted {
  border-color: rgba(143, 91, 31, 0.26);
  box-shadow: 0 18px 40px rgba(143, 91, 31, 0.12);
}

.report-workspace-alert,
.report-workspace-status,
.assist-alert {
  margin-bottom: 14px;
}

.report-model-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.model-select-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
}

.field-hint {
  margin-top: 6px;
  color: #7a6b45;
  font-size: 12px;
  line-height: 1.5;
}

.empty-thread {
  padding: 28px;
}

@media (max-width: 1200px) {
  .stage-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .thread-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 860px) {
  .thread-brief-head,
  .thread-brief-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .thread-brief-grid,
  .strategy-summary,
  .stage-grid,
  .report-model-grid {
    grid-template-columns: 1fr;
  }
}
</style>
