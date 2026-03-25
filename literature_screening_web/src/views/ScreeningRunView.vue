<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CircleDashed, FileUp, Save, WandSparkles, X } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NCheckbox,
  NDynamicInput,
  NForm,
  NFormItem,
  NGrid,
  NGridItem,
  NInput,
  NInputNumber,
  NSelect,
  NText,
  useMessage
} from 'naive-ui'
import { useDraftsStore } from '@/stores/drafts'
import { useMetaStore } from '@/stores/meta'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import { parseCriteriaMarkdown } from '@/utils/criteria'
import { strategyPlanToCriteriaMarkdown } from '@/utils/strategy'
import type { ModelSettings, ProviderName } from '@/types/api'

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
const selectedTemplateId = ref<string | null>(null)
const templateName = ref('')

const title = ref('new-screening-run')
const topic = ref('')
const inclusion = ref<string[]>([''])
const exclusion = ref<string[]>([''])
const criteriaMarkdown = ref('')
const provider = ref<ProviderName>('deepseek')
const model = ref<ModelSettings>({
  provider: 'deepseek',
  model_name: 'deepseek-chat',
  api_base_url: 'https://api.deepseek.com/v1',
  api_key_env: 'DEEPSEEK_API_KEY',
  api_key: '',
  temperature: 0,
  max_tokens: 1536,
  min_request_interval_seconds: 2
})
const batchSize = ref(10)
const targetIncludeCount = ref(30)
const stopWhenReached = ref(true)
const allowUncertain = ref(true)
const retryTimes = ref(6)
const requestTimeout = ref(240)
const encoding = ref('auto')
const files = ref<File[]>([])
const isDragging = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const hydratingDraft = ref(false)

const selectedPreset = computed(() => metaStore.providerPresets.find((item) => item.provider === provider.value))
const rememberedFileNames = computed(() => draftsStore.screeningDraft.fileNames)
const currentProject = computed(() =>
  projectsStore.currentProject?.id === selectedProjectId.value ? projectsStore.currentProject : null
)
const projectOptions = computed(() =>
  projectsStore.list.map((item) => ({
    label: `${item.name} · ${item.topic}`,
    value: item.id
  }))
)
const datasetOptions = computed(() =>
  (currentProject.value?.datasets ?? []).map((item) => ({
    label: `${item.label} · ${item.record_count ?? '-'} 篇 · ${item.kind}`,
    value: item.id
  }))
)
const templateOptions = computed(() =>
  projectsStore.templates.map((item) => ({
    label: item.name,
    value: item.id
  }))
)

function applyDraft() {
  const draft = draftsStore.screeningDraft
  selectedProjectId.value = draft.projectId
  newProjectName.value = draft.newProjectName
  newProjectDescription.value = draft.newProjectDescription
  sourceDatasetIds.value = [...draft.sourceDatasetIds]
  parentTaskId.value = draft.parentTaskId
  selectedTemplateId.value = draft.selectedTemplateId
  title.value = draft.title
  topic.value = draft.topic
  criteriaMarkdown.value = draft.criteriaMarkdown
  inclusion.value = draft.inclusion.length ? [...draft.inclusion] : ['']
  exclusion.value = draft.exclusion.length ? [...draft.exclusion] : ['']
  provider.value = draft.provider
  model.value = { ...draft.model }
  batchSize.value = draft.batchSize
  targetIncludeCount.value = draft.targetIncludeCount
  stopWhenReached.value = draft.stopWhenReached
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
  selectedTemplateId.value = null
  templateName.value = ''
  title.value = 'new-screening-run'
  topic.value = ''
  criteriaMarkdown.value = ''
  inclusion.value = ['']
  exclusion.value = ['']
  provider.value = 'deepseek'
  model.value = {
    provider: 'deepseek',
    model_name: 'deepseek-chat',
    api_base_url: 'https://api.deepseek.com/v1',
    api_key_env: 'DEEPSEEK_API_KEY',
    api_key: draftsStore.getProviderApiKey('deepseek'),
    temperature: 0,
    max_tokens: 1536,
    min_request_interval_seconds: 2
  }
  batchSize.value = 10
  targetIncludeCount.value = 30
  stopWhenReached.value = true
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
    selectedTemplateId: selectedTemplateId.value,
    title: title.value,
    topic: topic.value,
    criteriaMarkdown: criteriaMarkdown.value,
    inclusion: inclusion.value,
    exclusion: exclusion.value,
    provider: provider.value,
    model: model.value,
    batchSize: batchSize.value,
    targetIncludeCount: targetIncludeCount.value,
    stopWhenReached: stopWhenReached.value,
    allowUncertain: allowUncertain.value,
    retryTimes: retryTimes.value,
    requestTimeout: requestTimeout.value,
    encoding: encoding.value
  })
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
})

watch(selectedProjectId, async (nextProjectId) => {
  if (nextProjectId) {
    await projectsStore.loadProject(nextProjectId)
  }
  if (!hydratingDraft.value && !nextProjectId) {
    sourceDatasetIds.value = []
    selectedTemplateId.value = null
  }
})

watch(selectedTemplateId, (nextTemplateId) => {
  if (!nextTemplateId) return
  const template = projectsStore.templates.find((item) => item.id === nextTemplateId)
  if (!template) return
  const payload = template.payload as Record<string, unknown>
  if (typeof payload.topic === 'string') topic.value = payload.topic
  if (Array.isArray(payload.inclusion)) inclusion.value = payload.inclusion as string[]
  if (Array.isArray(payload.exclusion)) exclusion.value = payload.exclusion as string[]
  if (typeof payload.criteriaMarkdown === 'string') criteriaMarkdown.value = payload.criteriaMarkdown
  if (typeof payload.batchSize === 'number') batchSize.value = payload.batchSize
  if (typeof payload.targetIncludeCount === 'number') targetIncludeCount.value = payload.targetIncludeCount
  if (typeof payload.stopWhenReached === 'boolean') stopWhenReached.value = payload.stopWhenReached
  if (typeof payload.allowUncertain === 'boolean') allowUncertain.value = payload.allowUncertain
  if (typeof payload.retryTimes === 'number') retryTimes.value = payload.retryTimes
  if (typeof payload.requestTimeout === 'number') requestTimeout.value = payload.requestTimeout
  message.success(`已应用模板：${template.name}`)
})

watch(
  [
    selectedProjectId,
    newProjectName,
    newProjectDescription,
    sourceDatasetIds,
    parentTaskId,
    selectedTemplateId,
    title,
    topic,
    criteriaMarkdown,
    inclusion,
    exclusion,
    provider,
    model,
    batchSize,
    targetIncludeCount,
    stopWhenReached,
    allowUncertain,
    retryTimes,
    requestTimeout,
    encoding
  ],
  () => persistDraft(),
  { deep: true }
)

function parseCriteria() {
  const draft = parseCriteriaMarkdown(criteriaMarkdown.value)
  if (draft.topic) topic.value = draft.topic
  if (draft.inclusion.length) inclusion.value = draft.inclusion
  if (draft.exclusion.length) exclusion.value = draft.exclusion

  if (!draft.inclusion.length && !draft.exclusion.length) {
    message.warning('没有识别出纳入/排除标准。请检查 Markdown 是否包含“纳入标准”“排除标准”标题或对应的冒号写法。')
    return
  }

  if (draft.warnings.length) message.info(draft.warnings[0])
  else message.success('已解析到结构化字段。')
}

function buildCriteriaMarkdownFromStructured(nextTopic: string, nextInclusion: string[], nextExclusion: string[]) {
  const parts = ['# 主题', nextTopic || '', '', '# 纳入标准']
  for (const item of nextInclusion.filter(Boolean)) parts.push(`- ${item}`)
  parts.push('', '# 排除标准')
  for (const item of nextExclusion.filter(Boolean)) parts.push(`- ${item}`)
  return parts.join('\n').trim()
}

function applyStrategyPrefill(taskPayload: { title?: string | null; project_id?: string | null; project_topic?: string | null; strategy_plan?: { screening_topic: string; inclusion: string[]; exclusion: string[] } | null }) {
  if (!taskPayload.strategy_plan) return
  const plan = taskPayload.strategy_plan
  topic.value = plan.screening_topic || taskPayload.project_topic || topic.value
  inclusion.value = plan.inclusion.length ? [...plan.inclusion] : inclusion.value
  exclusion.value = plan.exclusion.length ? [...plan.exclusion] : exclusion.value
  criteriaMarkdown.value = strategyPlanToCriteriaMarkdown(plan)
  if (taskPayload.project_id) selectedProjectId.value = taskPayload.project_id
  if (!title.value || title.value === 'new-screening-run') {
    title.value = `${taskPayload.title || 'strategy'}-screening`
  }
}

function applyParentTaskPrefill(taskPayload: { title?: string | null; request_payload?: Record<string, unknown> | null; project_id?: string | null }) {
  const payload = taskPayload.request_payload ?? {}
  const inheritedTopic = typeof payload.topic === 'string' ? payload.topic : ''
  const inheritedInclusion = Array.isArray(payload.inclusion) ? payload.inclusion.filter((item): item is string => typeof item === 'string') : []
  const inheritedExclusion = Array.isArray(payload.exclusion) ? payload.exclusion.filter((item): item is string => typeof item === 'string') : []
  const inheritedProvider = typeof payload.provider === 'string' ? (payload.provider as ProviderName) : provider.value

  if (taskPayload.project_id) selectedProjectId.value = taskPayload.project_id
  if (!title.value || title.value === 'new-screening-run') {
    title.value = `${taskPayload.title || 'screening'}-continue`
  }
  if (inheritedTopic) topic.value = inheritedTopic
  if (typeof payload.criteria_markdown === 'string' && payload.criteria_markdown.trim()) {
    criteriaMarkdown.value = payload.criteria_markdown
  } else if (inheritedTopic || inheritedInclusion.length || inheritedExclusion.length) {
    criteriaMarkdown.value = buildCriteriaMarkdownFromStructured(inheritedTopic, inheritedInclusion, inheritedExclusion)
  }
  if (inheritedInclusion.length) inclusion.value = inheritedInclusion
  if (inheritedExclusion.length) exclusion.value = inheritedExclusion

  provider.value = inheritedProvider
  model.value = {
    ...model.value,
    provider: inheritedProvider,
    model_name: typeof payload.model_name === 'string' ? payload.model_name : model.value.model_name,
    api_base_url: typeof payload.api_base_url === 'string' ? payload.api_base_url : model.value.api_base_url,
    api_key_env: typeof payload.api_key_env === 'string' ? payload.api_key_env : model.value.api_key_env,
    temperature: typeof payload.temperature === 'number' ? payload.temperature : model.value.temperature,
    max_tokens: typeof payload.max_tokens === 'number' ? payload.max_tokens : model.value.max_tokens,
    min_request_interval_seconds:
      typeof payload.min_request_interval_seconds === 'number'
        ? payload.min_request_interval_seconds
        : model.value.min_request_interval_seconds,
    api_key: draftsStore.getProviderApiKey(inheritedProvider)
  }
  if (typeof payload.batch_size === 'number') batchSize.value = payload.batch_size
  if (typeof payload.target_include_count === 'number') targetIncludeCount.value = payload.target_include_count
  if (typeof payload.stop_when_target_reached === 'boolean') stopWhenReached.value = payload.stop_when_target_reached
  if (typeof payload.allow_uncertain === 'boolean') allowUncertain.value = payload.allow_uncertain
  if (typeof payload.retry_times === 'number') retryTimes.value = payload.retry_times
  if (typeof payload.request_timeout_seconds === 'number') requestTimeout.value = payload.request_timeout_seconds
  if (typeof payload.encoding === 'string') encoding.value = payload.encoding
}

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

async function saveCurrentAsTemplate() {
  if (!selectedProjectId.value || !templateName.value.trim()) {
    message.warning('先选择项目并填写模板名称。')
    return
  }
  await projectsStore.saveTemplate({
    name: templateName.value.trim(),
    project_id: selectedProjectId.value,
    payload: {
      topic: topic.value,
      inclusion: inclusion.value.filter(Boolean),
      exclusion: exclusion.value.filter(Boolean),
      criteriaMarkdown: criteriaMarkdown.value,
      batchSize: batchSize.value,
      targetIncludeCount: targetIncludeCount.value,
      stopWhenReached: stopWhenReached.value,
      allowUncertain: allowUncertain.value,
      retryTimes: retryTimes.value,
      requestTimeout: requestTimeout.value
    }
  })
  message.success('模板已保存。')
  templateName.value = ''
}

async function submit() {
  const task = await tasksStore.submitScreening({
    project_id: selectedProjectId.value,
    new_project_name: selectedProjectId.value ? '' : newProjectName.value,
    new_project_description: selectedProjectId.value ? '' : newProjectDescription.value,
    source_dataset_ids: sourceDatasetIds.value,
    parent_task_id: parentTaskId.value,
    title: title.value,
    topic: topic.value,
    criteria_markdown: criteriaMarkdown.value,
    inclusion: inclusion.value.filter(Boolean),
    exclusion: exclusion.value.filter(Boolean),
    model: model.value,
    batch_size: batchSize.value,
    target_include_count: targetIncludeCount.value,
    stop_when_target_reached: stopWhenReached.value,
    allow_uncertain: allowUncertain.value,
    retry_times: retryTimes.value,
    request_timeout_seconds: requestTimeout.value,
    encoding: encoding.value,
    files: files.value
  })
  draftsStore.clearScreeningDraft()
  message.success('初筛任务已创建。')
  if (task.project_id) {
    await router.push(`/threads/${task.project_id}`)
    return
  }
  await router.push(`/tasks/${task.id}`)
}

const hasInputSource = computed(() => files.value.length > 0 || sourceDatasetIds.value.length > 0)
const canSubmit = computed(() => {
  const hasProject = Boolean(selectedProjectId.value || newProjectName.value.trim())
  return hasProject && Boolean(topic.value.trim()) && inclusion.value.some(Boolean) && exclusion.value.some(Boolean) && hasInputSource.value
})

onMounted(async () => {
  draftsStore.hydrate()
  await Promise.all([metaStore.ensureLoaded(), projectsStore.refreshProjects()])
  const queryProjectId = typeof route.query.projectId === 'string' ? route.query.projectId : null
  const querySourceDatasetId = typeof route.query.sourceDatasetId === 'string' ? route.query.sourceDatasetId : null
  const queryParentTaskId = typeof route.query.parentTaskId === 'string' ? route.query.parentTaskId : null
  const queryStrategyTaskId = typeof route.query.strategyTaskId === 'string' ? route.query.strategyTaskId : null

  const launchedFromThreadContext = Boolean(queryProjectId || querySourceDatasetId || queryParentTaskId || queryStrategyTaskId)

  hydratingDraft.value = true
  if (launchedFromThreadContext) {
    resetToFreshForm(queryProjectId)
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
    await projectsStore.loadProject(selectedProjectId.value)
  }

  if (queryStrategyTaskId) {
    const strategyTask = await tasksStore.loadTask(queryStrategyTaskId, true)
    if (strategyTask?.kind === 'strategy' && strategyTask.strategy_plan) {
      applyStrategyPrefill(strategyTask)
      message.success('已从检索与筛选方案带入研究主题和筛选标准')
    }
  }

  if (queryParentTaskId) {
    const parentTask = await tasksStore.loadTask(queryParentTaskId, true)
    if (parentTask?.kind === 'screening') {
      applyParentTaskPrefill(parentTask)
      message.success('已自动继承上一轮筛选配置')
    }
  }

  if (!files.value.length && rememberedFileNames.value.length) {
    message.info('已恢复草稿内容。由于浏览器限制，已选文件需要重新选择一次。')
  }
})
</script>

<template>
  <div class="screening-view">
    <section class="screening-hero panel-surface">
      <div>
        <div class="eyebrow">Screening Composer</div>
        <h1>围绕项目、数据集和任务链创建新的初筛任务</h1>
        <p>同一个项目下的任务可以复用已有数据集。你可以直接从上一轮的 unused 数据集继续筛，也可以上传新文件补充输入源。</p>
      </div>
      <NAlert type="info" :show-icon="false">当前页面会自动保存为草稿；项目内模板可用于快速复用一套筛选标准。</NAlert>
    </section>

    <div class="screening-grid">
      <NCard title="项目与来源" class="panel-surface card-span-2">
        <NGrid :cols="2" :x-gap="18" :y-gap="12" responsive="screen" item-responsive>
          <NGridItem span="2 m:1">
            <NFormItem label="选择已有项目">
              <NSelect v-model:value="selectedProjectId" clearable :options="projectOptions" placeholder="选择项目，或留空后新建项目" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="来源数据集">
              <NSelect
                v-model:value="sourceDatasetIds"
                multiple
                clearable
                :disabled="!selectedProjectId"
                :options="datasetOptions"
                placeholder="可从 unused / included / cumulative 数据集继续"
              />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1" v-if="!selectedProjectId">
            <NFormItem label="新建项目名称">
              <NInput v-model:value="newProjectName" placeholder="例如：SCAP-BALF-病毒谱-免疫-预后" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1" v-if="!selectedProjectId">
            <NFormItem label="项目说明">
              <NInput v-model:value="newProjectDescription" placeholder="可选，用于记录项目范围和交付背景" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2">
            <NFormItem label="任务模板">
              <NGrid :cols="3" :x-gap="12" responsive="screen" item-responsive>
                <NGridItem span="2">
                  <NSelect
                    v-model:value="selectedTemplateId"
                    clearable
                    :disabled="!selectedProjectId"
                    :options="templateOptions"
                    placeholder="选择项目模板后自动填充筛选配置"
                  />
                </NGridItem>
                <NGridItem span="1">
                  <NInput v-model:value="templateName" :disabled="!selectedProjectId" placeholder="模板名称" />
                </NGridItem>
              </NGrid>
            </NFormItem>
            <NButton tertiary :disabled="!selectedProjectId" @click="saveCurrentAsTemplate">
              <template #icon>
                <Save :size="16" />
              </template>
              保存当前配置为模板
            </NButton>
          </NGridItem>
        </NGrid>
      </NCard>

      <NCard title="任务基本信息" class="panel-surface">
        <NForm label-placement="top">
          <NFormItem label="任务名称">
            <NInput v-model:value="title" />
          </NFormItem>
          <NFormItem label="研究主题">
            <NInput v-model:value="topic" placeholder="例如：SCAP 患者 BALF 病毒谱与免疫调控研究" />
          </NFormItem>
        </NForm>
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

      <NCard title="筛选标准" class="panel-surface card-span-2">
        <NGrid :cols="2" :x-gap="18" responsive="screen" item-responsive>
          <NGridItem span="2 m:1">
            <NForm label-placement="top">
              <NFormItem label="原始 Markdown 标准">
                <NInput v-model:value="criteriaMarkdown" type="textarea" :rows="14" placeholder="# 主题 / 纳入标准 / 排除标准" />
              </NFormItem>
              <NButton secondary type="primary" @click="parseCriteria">
                <template #icon>
                  <WandSparkles :size="16" />
                </template>
                解析到结构化字段
              </NButton>
            </NForm>
          </NGridItem>

          <NGridItem span="2 m:1">
            <NForm label-placement="top">
              <NFormItem label="纳入标准">
                <NDynamicInput v-model:value="inclusion" :min="1" />
              </NFormItem>
              <NFormItem label="排除标准">
                <NDynamicInput v-model:value="exclusion" :min="1" />
              </NFormItem>
            </NForm>
          </NGridItem>
        </NGrid>
      </NCard>

      <NCard title="模型与批处理" class="panel-surface card-span-2">
        <NGrid :cols="4" :x-gap="18" :y-gap="12" responsive="screen" item-responsive>
          <NGridItem span="2 m:1">
            <NFormItem label="模型提供商">
              <NSelect
                v-model:value="provider"
                :options="metaStore.providerPresets.map((item) => ({ label: item.label, value: item.provider }))"
              />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="默认预设">
              <NText depth="3">{{ selectedPreset?.label || '-' }}</NText>
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="模型名称">
              <NInput v-model:value="model.model_name" />
            </NFormItem>
          </NGridItem>
<NGridItem span="2 m:1">
            <NFormItem label="API Key 变量名">
              <NInput v-model:value="model.api_key_env" placeholder="例如：DEEPSEEK_API_KEY" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="API Key（本地缓存）">
              <NInput
                type="password"
                show-password-on="click"
                :value="model.api_key || ''"
                @update:value="(value) => { model.api_key = value; draftsStore.setProviderApiKey(provider, value) }"
                placeholder="可直接填写，仅保存在当前浏览器本地"
              />
            </NFormItem>
          </NGridItem>
          <NGridItem span="4">
            <NFormItem label="API Base URL">
              <NInput v-model:value="model.api_base_url" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="Batch size">
              <NInputNumber v-model:value="batchSize" :min="1" :max="50" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="目标纳入数">
              <NInputNumber v-model:value="targetIncludeCount" :min="1" :max="9999" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="最大 tokens">
              <NInputNumber v-model:value="model.max_tokens" :min="512" :max="8192" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="最小请求间隔（秒）">
              <NInputNumber v-model:value="model.min_request_interval_seconds" :min="0" :max="30" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="重试次数">
              <NInputNumber v-model:value="retryTimes" :min="0" :max="10" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="请求超时（秒）">
              <NInputNumber v-model:value="requestTimeout" :min="60" :max="600" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="输入编码">
              <NInput v-model:value="encoding" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <div class="toggles">
              <NCheckbox v-model:checked="stopWhenReached">达到目标后停止</NCheckbox>
              <NCheckbox v-model:checked="allowUncertain">保留 uncertain</NCheckbox>
            </div>
          </NGridItem>
        </NGrid>
      </NCard>
    </div>

    <div class="action-bar panel-surface">
      <div>
        <div class="action-title">提交为后台任务</div>
        <div class="action-copy">本任务将归属于一个项目，并记录其来源数据集、父任务和输出数据集，供后续继续筛选或生成报告。</div>
      </div>
      <NButton :disabled="!canSubmit || tasksStore.submitting" type="primary" size="large" @click="submit">
        <template #icon>
          <CircleDashed :size="16" />
        </template>
        创建初筛任务
      </NButton>
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

.screening-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.card-span-2 {
  grid-column: span 2;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 12px;
  color: #6a776c;
}

h1 {
  margin: 8px 0 12px;
  font-size: 34px;
}

p {
  color: #516056;
  line-height: 1.7;
}

.dropzone {
  display: grid;
  place-items: center;
  gap: 10px;
  min-height: 200px;
  border-radius: 20px;
  border: 1px dashed #b0a38b;
  background: linear-gradient(180deg, rgba(255, 253, 248, 0.8), rgba(236, 232, 220, 0.8));
  cursor: pointer;
  transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
}

.dropzone-active {
  transform: translateY(-2px);
  border-color: #2d6a4f;
  background: linear-gradient(180deg, rgba(233, 246, 236, 0.95), rgba(221, 238, 226, 0.95));
}

.hidden-input {
  display: none;
}

.dropzone-title {
  font-size: 18px;
  font-weight: 700;
}

.dropzone-copy {
  color: #69736a;
}

.draft-alert,
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
  background: rgba(45, 106, 79, 0.12);
  color: #28513e;
  font-size: 13px;
}

.file-pill-remove {
  border: none;
  background: transparent;
  color: inherit;
  padding: 0;
  display: inline-flex;
  cursor: pointer;
}

.toggles {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 26px;
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.action-title {
  font-weight: 700;
}

.action-copy {
  color: #667368;
  margin-top: 6px;
}

@media (max-width: 1100px) {
  .screening-grid {
    grid-template-columns: 1fr;
  }

  .card-span-2 {
    grid-column: span 1;
  }

  .action-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
