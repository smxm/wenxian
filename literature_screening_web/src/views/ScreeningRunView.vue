<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ArrowLeft, CircleDashed, FileUp, RefreshCw, X } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NDynamicInput,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NSwitch,
  NTag,
  useMessage
} from 'naive-ui'
import { useDraftsStore } from '@/stores/drafts'
import { useMetaStore } from '@/stores/meta'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import { fetchProviderModels } from '@/api/client'
import { buildCriteriaMarkdown, strategyPlanToCriteriaMarkdown } from '@/utils/strategy'
import type { DatasetRecord, ModelSettings, ProjectDetail, ProviderName } from '@/types/api'

const router = useRouter()
const route = useRoute()
const metaStore = useMetaStore()
const tasksStore = useTasksStore()
const draftsStore = useDraftsStore()
const projectsStore = useProjectsStore()
const message = useMessage()

const selectedProjectId = ref<string | null>(null)
const newProjectName = ref('')
const newProjectDescription = ref('')
const sourceDatasetIds = ref<string[]>([])
const parentTaskId = ref<string | null>(null)
const screeningTitle = ref('')

const topic = ref('')
const inclusion = ref<string[]>([''])
const exclusion = ref<string[]>([''])
const criteriaMarkdown = ref('')
const overrideThreadCriteria = ref(false)
const provider = ref<ProviderName>('deepseek')
const model = ref<ModelSettings>({
  provider: 'deepseek',
  model_name: 'deepseek-chat',
  api_base_url: 'https://api.deepseek.com/v1',
  api_key_env: 'DEEPSEEK_API_KEY',
  api_key: '',
  temperature: 0,
  max_tokens: 4096,
  min_request_interval_seconds: 2
})
const modelOptions = ref<Array<{ label: string; value: string }>>([])
const modelsLoading = ref(false)
const modelFetchError = ref('')
const batchSize = ref(10)
const targetIncludeCount = ref<number | null>(null)
const stopWhenReached = ref(false)
const minIncludeConfidence = ref(0.8)
const syncingTargetControls = ref(false)
const allowUncertain = ref(true)
const retryTimes = ref(6)
const requestTimeout = ref(240)
const encoding = ref('auto')
const files = ref<File[]>([])
const isDragging = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const hydratingDraft = ref(false)
let modelRequestToken = 0
let modelReloadTimer: number | null = null
const routeProjectId = computed(() => {
  if (typeof route.params.projectId === 'string') return route.params.projectId
  if (typeof route.query.projectId === 'string') return route.query.projectId
  return null
})

const currentProject = computed<ProjectDetail | null>(() =>
  projectsStore.currentProject?.id === selectedProjectId.value ? projectsStore.currentProject : null
)
const taskTitleById = computed(() =>
  new Map((currentProject.value?.tasks ?? []).map((task) => [task.id, task.title]))
)
const isThreadScoped = computed(() => Boolean(routeProjectId.value))
const threadHomePath = computed(() => (selectedProjectId.value ? `/threads/${selectedProjectId.value}` : null))
const threadDefaults = computed(() => currentProject.value?.thread_profile?.screening ?? null)
const rememberedFileNames = computed(() => draftsStore.screeningDraft.fileNames)
const selectedPreset = computed(() => metaStore.providerPresets.find((item) => item.provider === provider.value))
const pageTitle = computed(() => (isThreadScoped.value ? '开始本线程的新一轮初筛' : '先选择线程，再开始新的初筛轮次'))
const pageCopy = computed(() =>
  isThreadScoped.value
    ? '设置本轮来源、文件和运行参数。'
    : '先选线程，再设置本轮来源和文件。'
)
const projectOptions = computed(() =>
  projectsStore.list.map((item) => ({
    label: `${item.name} · ${item.topic}`,
    value: item.id
  }))
)
const defaultTaskTitle = computed(() => {
  if (selectedProjectId.value && currentProject.value) {
    const roundCount = currentProject.value.tasks.filter((task) => task.kind === 'screening').length + 1
    return `${currentProject.value.name}-round-${roundCount}`
  }
  return `${newProjectName.value.trim() || 'new-thread'}-screening`
})
const effectiveTaskTitle = computed(() => screeningTitle.value.trim() || defaultTaskTitle.value)
const includeConfidenceOptions = [
  { label: '严格 · 90%以上', value: 0.9 },
  { label: '标准 · 80%以上', value: 0.8 },
  { label: '宽松 · 60%以上', value: 0.6 },
  { label: '模型判定即可', value: 0 }
]
const minIncludeConfidenceLabel = computed(() => (minIncludeConfidence.value > 0 ? `${Math.round(minIncludeConfidence.value * 100)}%` : '模型判定'))
const includeConfidenceHint = computed(() =>
  minIncludeConfidence.value > 0
    ? `模型判为纳入且相关度达到 ${minIncludeConfidenceLabel.value} 才进入纳入集。`
    : '模型判为纳入即可进入纳入集。'
)
const includeConfidenceTag = computed(() =>
  minIncludeConfidence.value > 0 ? `纳入≥${minIncludeConfidenceLabel.value}` : '模型判定纳入'
)

function fallbackModelOptions(nextProvider: ProviderName = provider.value) {
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

function setFallbackModelOptions(nextProvider: ProviderName = provider.value) {
  modelOptions.value = fallbackModelOptions(nextProvider)
  if (!modelOptions.value.some((option) => option.value === model.value.model_name)) {
    model.value = {
      ...model.value,
      model_name: modelOptions.value[0]?.value || model.value.model_name
    }
  }
}

async function loadModelOptions(options: { silent?: boolean } = {}) {
  const requestToken = ++modelRequestToken
  const currentProvider = provider.value
  const currentModel = { ...model.value }
  modelsLoading.value = true
  modelFetchError.value = ''
  try {
    const response = await fetchProviderModels({
      provider: currentProvider,
      api_base_url: currentModel.api_base_url,
      api_key_env: currentModel.api_key_env,
      api_key: currentModel.api_key || null
    })
    if (requestToken !== modelRequestToken || currentProvider !== provider.value) return
    const providerOptions = response.models.map((item) => ({
      label: item.label || item.id,
      value: item.id
    }))
    modelOptions.value = providerOptions.length ? providerOptions : fallbackModelOptions(currentProvider)
    if (!modelOptions.value.some((option) => option.value === model.value.model_name)) {
      model.value = {
        ...model.value,
        model_name: modelOptions.value[0]?.value || model.value.model_name
      }
    }
    modelFetchError.value = response.source === 'fallback' && response.error ? '未能从服务商获取模型，已使用默认模型。' : ''
  } catch {
    if (requestToken !== modelRequestToken || currentProvider !== provider.value) return
    setFallbackModelOptions(currentProvider)
    modelFetchError.value = '未能从服务商获取模型，已使用默认模型。'
  } finally {
    if (requestToken === modelRequestToken) {
      modelsLoading.value = false
    }
  }
  if (!options.silent && modelFetchError.value) {
    message.warning(modelFetchError.value)
  }
}

function scheduleModelReload() {
  if (typeof window === 'undefined') return
  if (modelReloadTimer !== null) window.clearTimeout(modelReloadTimer)
  modelReloadTimer = window.setTimeout(() => {
    modelReloadTimer = null
    void loadModelOptions({ silent: true })
  }, 700)
}

function updateModelApiKey(value: string) {
  model.value.api_key = value
  draftsStore.setProviderApiKey(provider.value, value)
  scheduleModelReload()
}

function screeningMaxTokens(value: number | null | undefined) {
  return Math.max(value ?? 4096, 4096)
}

function friendlyDatasetLabel(kind: string) {
  switch (kind) {
    case 'included_reviewed':
      return '人工复核后纳入'
    case 'included':
      return '本轮纳入'
    case 'unused':
      return '上一轮未使用'
    case 'cumulative_included':
      return '线程累计纳入'
    case 'fulltext_ready':
      return '已获取全文'
    case 'report_source':
      return '旧版报告输入'
    default:
      return kind
  }
}

function datasetOptionLabel(dataset: DatasetRecord) {
  const kindLabel = friendlyDatasetLabel(dataset.kind)
  const countLabel = `${dataset.record_count ?? '-'} 篇`
  const taskTitle = dataset.task_id ? taskTitleById.value.get(dataset.task_id) : ''
  if (taskTitle) return `${taskTitle} · ${kindLabel} · ${countLabel}`
  return `${kindLabel} · ${countLabel}`
}

const datasetOptions = computed(() =>
  (currentProject.value?.datasets ?? []).map((item) => ({
    label: datasetOptionLabel(item),
    value: item.id
  }))
)

const hasInputSource = computed(() => files.value.length > 0 || sourceDatasetIds.value.length > 0)
const canSubmit = computed(() => {
  return Boolean(selectedProjectId.value) && hasInputSource.value && Boolean(topic.value.trim()) && inclusion.value.some(Boolean) && exclusion.value.some(Boolean)
})

function syncTargetControls(nextTargetIncludeCount: number | null, nextStopWhenReached = false) {
  syncingTargetControls.value = true
  targetIncludeCount.value = nextTargetIncludeCount
  stopWhenReached.value = nextTargetIncludeCount ? nextStopWhenReached : false
  syncingTargetControls.value = false
}

function applyDraft() {
  const draft = draftsStore.screeningDraft
  selectedProjectId.value = routeProjectId.value ?? draft.projectId
  newProjectName.value = ''
  newProjectDescription.value = ''
  sourceDatasetIds.value = [...draft.sourceDatasetIds]
  parentTaskId.value = draft.parentTaskId
  screeningTitle.value = draft.title
  topic.value = draft.topic
  criteriaMarkdown.value = draft.criteriaMarkdown
  inclusion.value = draft.inclusion.length ? [...draft.inclusion] : ['']
  exclusion.value = draft.exclusion.length ? [...draft.exclusion] : ['']
  provider.value = draft.provider
  model.value = { ...draft.model, max_tokens: screeningMaxTokens(draft.model.max_tokens) }
  setFallbackModelOptions(draft.provider)
  void loadModelOptions({ silent: true })
  batchSize.value = draft.batchSize
  syncTargetControls(draft.targetIncludeCount, draft.stopWhenReached)
  minIncludeConfidence.value = draft.minIncludeConfidence ?? 0.8
  allowUncertain.value = draft.allowUncertain
  retryTimes.value = draft.retryTimes
  requestTimeout.value = draft.requestTimeout
  encoding.value = draft.encoding
  files.value = [...draftsStore.screeningFiles]
}

function resetToFreshForm(nextProjectId: string | null = null) {
  selectedProjectId.value = nextProjectId
  newProjectName.value = ''
  newProjectDescription.value = ''
  sourceDatasetIds.value = []
  parentTaskId.value = null
  screeningTitle.value = ''
  topic.value = ''
  criteriaMarkdown.value = ''
  inclusion.value = ['']
  exclusion.value = ['']
  overrideThreadCriteria.value = false
  provider.value = 'deepseek'
  model.value = {
    provider: 'deepseek',
    model_name: 'deepseek-chat',
    api_base_url: 'https://api.deepseek.com/v1',
    api_key_env: 'DEEPSEEK_API_KEY',
    api_key: draftsStore.getProviderApiKey('deepseek'),
    temperature: 0,
    max_tokens: 4096,
    min_request_interval_seconds: 2
  }
  setFallbackModelOptions('deepseek')
  void loadModelOptions({ silent: true })
  batchSize.value = 10
  syncTargetControls(null, false)
  minIncludeConfidence.value = 0.8
  allowUncertain.value = true
  retryTimes.value = 6
  requestTimeout.value = 240
  encoding.value = 'auto'
  files.value = []
  draftsStore.setScreeningFiles([])
}

function persistDraft() {
  draftsStore.updateScreeningDraft({
    projectId: selectedProjectId.value,
    newProjectName: newProjectName.value,
    newProjectDescription: newProjectDescription.value,
    sourceDatasetIds: sourceDatasetIds.value,
    parentTaskId: parentTaskId.value,
    selectedTemplateId: null,
    title: screeningTitle.value,
    topic: topic.value,
    criteriaMarkdown: criteriaMarkdown.value,
    inclusion: inclusion.value,
    exclusion: exclusion.value,
    provider: provider.value,
    model: { ...model.value, max_tokens: screeningMaxTokens(model.value.max_tokens) },
    batchSize: batchSize.value,
    targetIncludeCount: targetIncludeCount.value,
    stopWhenReached: stopWhenReached.value,
    minIncludeConfidence: minIncludeConfidence.value,
    allowUncertain: allowUncertain.value,
    retryTimes: retryTimes.value,
    requestTimeout: requestTimeout.value,
    encoding: encoding.value
  })
}

function applyThreadDefaults(project: ProjectDetail) {
  const defaults = project.thread_profile?.screening
  if (!defaults) return
  topic.value = defaults.topic || project.topic
  inclusion.value = defaults.inclusion.length ? [...defaults.inclusion] : ['']
  exclusion.value = defaults.exclusion.length ? [...defaults.exclusion] : ['']
  criteriaMarkdown.value = defaults.criteria_markdown || buildCriteriaMarkdown(topic.value, inclusion.value, exclusion.value)
  if (defaults.model) {
    provider.value = defaults.model.provider
    model.value = {
      ...model.value,
      ...defaults.model,
      api_key: draftsStore.getProviderApiKey(defaults.model.provider),
      max_tokens: screeningMaxTokens(defaults.model.max_tokens)
    }
    setFallbackModelOptions(defaults.model.provider)
    void loadModelOptions({ silent: true })
  }
  batchSize.value = defaults.batch_size ?? 10
  syncTargetControls(defaults.target_include_count ?? null, defaults.stop_when_target_reached)
  minIncludeConfidence.value = defaults.min_include_confidence ?? 0.8
  allowUncertain.value = defaults.allow_uncertain
  retryTimes.value = defaults.retry_times
  requestTimeout.value = defaults.request_timeout_seconds
  encoding.value = defaults.encoding
  overrideThreadCriteria.value = false
}

function refreshCriteriaMarkdown() {
  criteriaMarkdown.value = buildCriteriaMarkdown(topic.value, inclusion.value.filter(Boolean), exclusion.value.filter(Boolean))
}

function applyStrategyPrefill(taskPayload: { title?: string | null; project_id?: string | null; project_topic?: string | null; strategy_plan?: { screening_topic: string; inclusion: string[]; exclusion: string[] } | null }) {
  if (!taskPayload.strategy_plan) return
  overrideThreadCriteria.value = true
  topic.value = taskPayload.strategy_plan.screening_topic || taskPayload.project_topic || topic.value
  inclusion.value = taskPayload.strategy_plan.inclusion.length ? [...taskPayload.strategy_plan.inclusion] : inclusion.value
  exclusion.value = taskPayload.strategy_plan.exclusion.length ? [...taskPayload.strategy_plan.exclusion] : exclusion.value
  criteriaMarkdown.value = strategyPlanToCriteriaMarkdown(taskPayload.strategy_plan)
  if (taskPayload.project_id) selectedProjectId.value = taskPayload.project_id
}

function applyParentTaskPrefill(taskPayload: { request_payload?: Record<string, unknown> | null; project_id?: string | null }) {
  const payload = taskPayload.request_payload ?? {}
  const inheritedTopic = typeof payload.topic === 'string' ? payload.topic : ''
  const inheritedInclusion = Array.isArray(payload.inclusion) ? payload.inclusion.filter((item): item is string => typeof item === 'string') : []
  const inheritedExclusion = Array.isArray(payload.exclusion) ? payload.exclusion.filter((item): item is string => typeof item === 'string') : []
  overrideThreadCriteria.value = true
  if (taskPayload.project_id) selectedProjectId.value = taskPayload.project_id
  if (inheritedTopic) topic.value = inheritedTopic
  if (typeof payload.criteria_markdown === 'string' && payload.criteria_markdown.trim()) {
    criteriaMarkdown.value = payload.criteria_markdown
  }
  if (inheritedInclusion.length) inclusion.value = inheritedInclusion
  if (inheritedExclusion.length) exclusion.value = inheritedExclusion
  if (typeof payload.batch_size === 'number') batchSize.value = payload.batch_size
  if (typeof payload.min_include_confidence === 'number') minIncludeConfidence.value = payload.min_include_confidence
  const inheritedTargetIncludeCount = typeof payload.target_include_count === 'number' ? payload.target_include_count : null
  const inheritedStopWhenReached = typeof payload.stop_when_target_reached === 'boolean' ? payload.stop_when_target_reached : false
  if (inheritedTargetIncludeCount !== null || typeof payload.stop_when_target_reached === 'boolean') {
    syncTargetControls(inheritedTargetIncludeCount, inheritedStopWhenReached)
  }
}

watch(provider, (nextProvider) => {
  if (hydratingDraft.value) return
  const preset = metaStore.providerPresets.find((item) => item.provider === nextProvider)
  if (!preset) return
  model.value = {
    ...model.value,
    provider: preset.provider,
    model_name: preset.defaultModel,
    api_base_url: preset.defaultBaseUrl,
    api_key_env: preset.defaultApiKeyEnv,
    api_key: draftsStore.getProviderApiKey(preset.provider)
  }
  setFallbackModelOptions(preset.provider)
  void loadModelOptions({ silent: true })
})

watch(selectedProjectId, async (nextProjectId, previousProjectId) => {
  if (!nextProjectId) {
    if (previousProjectId) sourceDatasetIds.value = []
    return
  }
  const project = await projectsStore.loadProject(nextProjectId)
  if (project && !hydratingDraft.value) {
    applyThreadDefaults(project)
  }
})

watch([topic, inclusion, exclusion], () => {
  if (!overrideThreadCriteria.value) return
  refreshCriteriaMarkdown()
}, { deep: true })

watch(targetIncludeCount, (nextValue, previousValue) => {
  if (syncingTargetControls.value) return
  if (nextValue === null) {
    stopWhenReached.value = false
    return
  }
  if (previousValue === null) {
    stopWhenReached.value = true
  }
}, { flush: 'sync' })

watch(
  [
    selectedProjectId,
    newProjectName,
    newProjectDescription,
    sourceDatasetIds,
    parentTaskId,
    screeningTitle,
    topic,
    criteriaMarkdown,
    inclusion,
    exclusion,
    provider,
    model,
    batchSize,
    targetIncludeCount,
    stopWhenReached,
    minIncludeConfidence,
    allowUncertain,
    retryTimes,
    requestTimeout,
    encoding
  ],
  () => persistDraft(),
  { deep: true }
)

function setFiles(nextFiles: File[]) {
  files.value = nextFiles
  draftsStore.setScreeningFiles(nextFiles)
  if (nextFiles.length) message.success(`已选择 ${nextFiles.length} 个文件。`)
}

function mergeFiles(currentFiles: File[], incomingFiles: File[]) {
  const merged = [...currentFiles]
  const seen = new Set(currentFiles.map((file) => `${file.name}::${file.size}::${file.lastModified}`))
  for (const file of incomingFiles) {
    const key = `${file.name}::${file.size}::${file.lastModified}`
    if (seen.has(key)) continue
    seen.add(key)
    merged.push(file)
  }
  return merged
}

function removeFile(index: number) {
  const nextFiles = files.value.filter((_, current) => current !== index)
  setFiles(nextFiles)
}

function clearFiles() {
  setFiles([])
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const selectedFiles = Array.from(input.files ?? [])
  if (!selectedFiles.length) return
  setFiles(mergeFiles(files.value, selectedFiles))
  input.value = ''
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragging.value = false
  const droppedFiles = Array.from(event.dataTransfer?.files ?? [])
  if (!droppedFiles.length) return
  setFiles(mergeFiles(files.value, droppedFiles))
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  isDragging.value = true
}

function handleDragLeave() {
  isDragging.value = false
}

function openFilePicker() {
  fileInputRef.value?.click()
}

function resetCriteriaToThreadDefaults() {
  if (!currentProject.value) return
  applyThreadDefaults(currentProject.value)
  message.success('已恢复线程默认主题与筛选标准')
}

async function submit() {
  refreshCriteriaMarkdown()
  const task = await tasksStore.submitScreening({
    project_id: selectedProjectId.value,
    new_project_name: '',
    new_project_description: '',
    source_dataset_ids: sourceDatasetIds.value,
    parent_task_id: parentTaskId.value,
    title: effectiveTaskTitle.value,
    topic: topic.value,
    criteria_markdown: criteriaMarkdown.value,
    inclusion: inclusion.value.filter(Boolean),
    exclusion: exclusion.value.filter(Boolean),
    model: { ...model.value, max_tokens: screeningMaxTokens(model.value.max_tokens) },
    batch_size: batchSize.value,
    target_include_count: targetIncludeCount.value,
    stop_when_target_reached: Boolean(targetIncludeCount.value && stopWhenReached.value),
    min_include_confidence: minIncludeConfidence.value,
    allow_uncertain: allowUncertain.value,
    retry_times: retryTimes.value,
    request_timeout_seconds: requestTimeout.value,
    encoding: encoding.value,
    files: files.value
  })
  draftsStore.clearScreeningDraft()
  message.success('初筛任务已创建')
  if (task.project_id) {
    await router.push(`/threads/${task.project_id}`)
    return
  }
  await router.push(`/tasks/${task.id}`)
}

onMounted(async () => {
  draftsStore.hydrate()
  await Promise.all([metaStore.ensureLoaded(), projectsStore.refreshProjects()])
  const querySourceDatasetId = typeof route.query.sourceDatasetId === 'string' ? route.query.sourceDatasetId : null
  const queryParentTaskId = typeof route.query.parentTaskId === 'string' ? route.query.parentTaskId : null
  const queryStrategyTaskId = typeof route.query.strategyTaskId === 'string' ? route.query.strategyTaskId : null

  const launchedFromThreadContext = Boolean(routeProjectId.value || querySourceDatasetId || queryParentTaskId || queryStrategyTaskId)

  hydratingDraft.value = true
  if (launchedFromThreadContext) {
    resetToFreshForm(routeProjectId.value)
    if (querySourceDatasetId) sourceDatasetIds.value = [querySourceDatasetId]
    if (queryParentTaskId) parentTaskId.value = queryParentTaskId
  } else {
    applyDraft()
    if (!model.value.api_key) {
      model.value.api_key = draftsStore.getProviderApiKey(provider.value)
    }
  }
  hydratingDraft.value = false

  if (selectedProjectId.value) {
    const project = await projectsStore.loadProject(selectedProjectId.value)
    if (project) applyThreadDefaults(project)
  }

  if (queryStrategyTaskId) {
    const strategyTask = await tasksStore.loadTask(queryStrategyTaskId, true)
    if (strategyTask?.kind === 'strategy' && strategyTask.strategy_plan) {
      applyStrategyPrefill(strategyTask)
      message.success('已带入方案生成的主题与筛选标准')
    }
  }

  if (queryParentTaskId) {
    const parentTask = await tasksStore.loadTask(queryParentTaskId, true)
    if (parentTask?.kind === 'screening') {
      applyParentTaskPrefill(parentTask)
      message.success('已继承上一轮筛选设置')
    }
  }

  if (!files.value.length && rememberedFileNames.value.length) {
    message.info('已恢复草稿内容。由于浏览器限制，已选文件需要重新选择一次。')
  }
})

onUnmounted(() => {
  if (modelReloadTimer !== null && typeof window !== 'undefined') {
    window.clearTimeout(modelReloadTimer)
  }
})
</script>

<template>
  <div class="screening-view">
    <section class="screening-hero panel-surface">
      <div>
        <div class="eyebrow">Screening Round</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageCopy }}</p>
      </div>
      <div class="hero-actions">
        <RouterLink v-if="threadHomePath" :to="threadHomePath">
          <NButton tertiary>
            <template #icon><ArrowLeft :size="16" /></template>
            返回线程主页
          </NButton>
        </RouterLink>
      </div>
    </section>

    <div class="screening-grid">
      <NCard :title="isThreadScoped ? '当前线程与来源' : '选择线程与来源'" class="panel-surface">
        <div v-if="isThreadScoped && currentProject" class="thread-context-block">
          <div class="thread-context-title">{{ currentProject.name }}</div>
          <div class="thread-context-copy">{{ currentProject.description || '当前线程' }}</div>
          <div class="thread-context-tags">
            <NTag round>当前主题：{{ currentProject.thread_profile?.screening.topic || currentProject.topic }}</NTag>
            <NTag round type="success">已有 {{ currentProject.tasks.filter((task) => task.kind === 'screening').length }} 轮初筛</NTag>
          </div>
        </div>

        <NForm label-placement="top">
          <NFormItem v-if="!isThreadScoped" label="选择要继续的线程">
            <NSelect
              v-model:value="selectedProjectId"
              clearable
              :options="projectOptions"
              placeholder="先选一条线程，再开始这一轮初筛"
            />
          </NFormItem>
          <NFormItem label="继续使用已有结果">
            <NSelect
              v-model:value="sourceDatasetIds"
              multiple
              clearable
              :disabled="!selectedProjectId"
              :options="datasetOptions"
              placeholder="可选；如果同时上传文件，系统会把两部分合并后一起筛选"
            />
          </NFormItem>
          <NFormItem label="初筛名称">
            <NInput v-model:value="screeningTitle" :placeholder="`留空则自动命名为 ${defaultTaskTitle}`" />
            <div class="field-hint">当前将保存为：{{ effectiveTaskTitle }}</div>
          </NFormItem>
        </NForm>

        <NAlert v-if="!selectedProjectId" type="warning" :show-icon="false">
          先选择线程。
        </NAlert>
        <NAlert v-else-if="!isThreadScoped" type="info" :show-icon="false">
          也可以从线程主页进入。
        </NAlert>
      </NCard>

      <NCard title="当前主题与筛选标准" class="panel-surface">
        <div v-if="threadDefaults" class="criteria-preview">
          <div class="criteria-head">
            <div>
              <div class="criteria-title">{{ threadDefaults.topic || currentProject?.topic || '未设置线程主题' }}</div>
              <div class="criteria-copy">本轮默认沿用这套主题和标准。</div>
            </div>
            <div class="criteria-actions">
              <NButton tertiary size="small" @click="overrideThreadCriteria = !overrideThreadCriteria">
                {{ overrideThreadCriteria ? '收起临时修改' : '本轮临时修改' }}
              </NButton>
              <NButton v-if="overrideThreadCriteria" tertiary size="small" @click="resetCriteriaToThreadDefaults">恢复默认</NButton>
            </div>
          </div>

          <div class="criteria-tags">
            <NTag round type="success">纳入 {{ threadDefaults.inclusion.length }}</NTag>
            <NTag round type="warning">排除 {{ threadDefaults.exclusion.length }}</NTag>
            <NTag round>{{ currentProject?.thread_profile?.strategy.selected_databases.length || 0 }} 个数据库检索式</NTag>
          </div>
        </div>

        <NAlert v-else type="warning" :show-icon="false">
          当前线程还没有主题和标准。
        </NAlert>

        <div v-if="overrideThreadCriteria || !threadDefaults" class="criteria-editor">
          <NForm label-placement="top">
            <NFormItem label="本轮主题">
              <NInput v-model:value="topic" placeholder="本轮筛选使用的主题" />
            </NFormItem>
            <NFormItem label="纳入标准">
              <NDynamicInput v-model:value="inclusion" :min="1" />
            </NFormItem>
            <NFormItem label="排除标准">
              <NDynamicInput v-model:value="exclusion" :min="1" />
            </NFormItem>
          </NForm>
        </div>
      </NCard>

      <NCard title="输入文件" class="panel-surface">
        <div
          class="dropzone"
          :class="{ 'dropzone-active': isDragging }"
          @click="openFilePicker"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @drop="handleDrop"
        >
          <input ref="fileInputRef" class="hidden-input" type="file" multiple @change="handleFileChange" />
          <FileUp :size="22" />
          <div class="dropzone-title">拖入或选择文献文件</div>
          <div class="dropzone-copy">{{ metaStore.acceptedInputFormats.join(' / ') || '.bib / .ris / .enw / .txt' }}</div>
        </div>

        <NAlert v-if="rememberedFileNames.length && !files.length" type="warning" :show-icon="false" class="draft-alert">
          已恢复草稿中的文件名：{{ rememberedFileNames.join('，') }}。文件内容不能跨刷新恢复，请重新选择文件。
        </NAlert>

        <div class="file-toolbar" v-if="files.length">
          <NButton tertiary size="small" @click="clearFiles">清空全部文件</NButton>
        </div>

        <div class="file-list" v-if="files.length">
          <div v-for="(file, index) in files" :key="`${file.name}-${index}`" class="file-pill">
            <span>{{ file.name }}</span>
            <button class="file-pill-remove" type="button" @click.stop="removeFile(index)">
              <X :size="12" />
            </button>
          </div>
        </div>
      </NCard>

      <NCard title="模型与批次" class="panel-surface">
        <NForm label-placement="top">
          <NFormItem label="模型提供商">
            <NSelect
              v-model:value="provider"
              :options="metaStore.providerPresets.map((item) => ({ label: item.label, value: item.provider }))"
            />
          </NFormItem>
          <NFormItem label="模型名称">
            <div class="model-select-row">
              <NSelect
                v-model:value="model.model_name"
                filterable
                :loading="modelsLoading"
                :options="modelOptions"
              />
              <NButton tertiary :loading="modelsLoading" @click="loadModelOptions()">
                <template #icon><RefreshCw :size="16" /></template>
              </NButton>
            </div>
            <div v-if="modelFetchError" class="field-hint">{{ modelFetchError }}</div>
          </NFormItem>
          <NFormItem label="API Key">
            <NInput
              type="password"
              show-password-on="click"
              :value="model.api_key || ''"
              @update:value="updateModelApiKey"
              @blur="loadModelOptions({ silent: true })"
              placeholder="仅保存在当前浏览器本地"
            />
          </NFormItem>
          <NFormItem label="批次大小">
            <NInputNumber v-model:value="batchSize" :min="1" :max="50" />
          </NFormItem>
          <NFormItem label="最低纳入相关度">
            <NSelect
              v-model:value="minIncludeConfidence"
              :options="includeConfidenceOptions"
            />
            <div class="field-hint">
              {{ includeConfidenceHint }}
            </div>
          </NFormItem>
          <NFormItem label="目标纳入数">
            <NInputNumber
              v-model:value="targetIncludeCount"
              clearable
              :min="1"
              :max="9999"
              placeholder="留空表示整批全部筛选"
            />
          </NFormItem>
          <NFormItem label="达到目标后停止">
            <div class="target-stop-row">
              <NSwitch v-model:value="stopWhenReached" :disabled="!targetIncludeCount" />
              <span class="field-hint inline-hint">
                {{
                  targetIncludeCount
                    ? (stopWhenReached ? `累计纳入达到 ${targetIncludeCount} 篇后提前结束本轮` : `即使达到 ${targetIncludeCount} 篇也继续筛完整个输入集`)
                    : '先填写目标纳入数，再决定是否提前停止'
                }}
              </span>
            </div>
          </NFormItem>
        </NForm>

        <div class="setting-tags">
          <NTag round>{{ selectedPreset?.label || provider }}</NTag>
          <NTag round type="success">Batch {{ batchSize }}</NTag>
          <NTag round type="info">{{ includeConfidenceTag }}</NTag>
          <NTag round type="warning">{{ targetIncludeCount ? `目标纳入 ${targetIncludeCount}` : '全部筛选' }}</NTag>
          <NTag v-if="targetIncludeCount" round :type="stopWhenReached ? 'success' : 'info'">
            {{ stopWhenReached ? '达到目标后停止' : '达到目标后继续筛选' }}
          </NTag>
        </div>
      </NCard>
    </div>

    <div class="action-bar panel-surface">
      <div>
        <div class="action-title">提交为新的初筛轮次</div>
        <div class="action-copy">提交后会生成新的初筛轮次。</div>
      </div>
      <NSpace>
        <RouterLink v-if="threadHomePath" :to="threadHomePath">
          <NButton tertiary>返回线程主页</NButton>
        </RouterLink>
        <NButton :disabled="!canSubmit || tasksStore.submitting" type="primary" size="large" @click="submit">
          <template #icon>
            <CircleDashed :size="16" />
          </template>
          创建初筛任务
        </NButton>
      </NSpace>
    </div>
  </div>
</template>

<style scoped>
.screening-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.screening-hero,
.action-bar {
  padding: 24px;
}

.hero-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.screening-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.thread-context-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 18px;
}

.thread-context-title,
.criteria-title,
.action-title {
  font-weight: 700;
}

.thread-context-copy,
.criteria-copy,
.action-copy {
  color: #5b665d;
}

.thread-context-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.criteria-preview,
.criteria-editor {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #6a776c;
}

.inline-hint {
  margin-top: 0;
}

.model-select-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
}

.criteria-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.criteria-actions,
.criteria-tags,
.setting-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.target-stop-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dropzone {
  border: 1px dashed rgba(71, 95, 76, 0.22);
  border-radius: 18px;
  padding: 26px 20px;
  display: grid;
  justify-items: center;
  gap: 8px;
  cursor: pointer;
  background: rgba(247, 249, 246, 0.92);
  transition: all 0.2s ease;
}

.dropzone-active {
  border-color: rgba(45, 106, 79, 0.46);
  background: rgba(232, 242, 234, 0.96);
}

.dropzone-title {
  font-weight: 700;
}

.dropzone-copy {
  color: #6a776c;
}

.hidden-input {
  display: none;
}

.draft-alert {
  margin-top: 14px;
}

.file-toolbar {
  margin-top: 14px;
}

.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.file-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(232, 242, 234, 0.96);
  border: 1px solid rgba(45, 106, 79, 0.16);
}

.file-pill-remove {
  border: 0;
  background: transparent;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  padding: 0;
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

@media (max-width: 960px) {
  .screening-grid {
    grid-template-columns: 1fr;
  }

  .criteria-head,
  .action-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
