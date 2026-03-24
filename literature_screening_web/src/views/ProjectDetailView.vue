<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import dayjs from 'dayjs'
import { FileSearch, FileText, GitBranchPlus, Pencil, RefreshCw, Trash2, WandSparkles } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NSelect,
  NSpace,
  NTag,
  useMessage
} from 'naive-ui'
import OverviewMetric from '@/components/OverviewMetric.vue'
import ThreadMessageCard from '@/components/ThreadMessageCard.vue'
import { getArtifactUrl } from '@/api/client'
import { useDraftsStore } from '@/stores/drafts'
import { useMetaStore } from '@/stores/meta'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import type { DatasetRecord, TaskArtifact, TaskSnapshot } from '@/types/api'
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

const reportTitle = ref('')
const reportTopic = ref('')
const reportName = ref('simple_report')
const reportDatasetIds = ref<string[]>([])
const reportReferenceStyle = ref<'gbt7714' | 'apa7'>('gbt7714')
const pollTimer = ref<number | null>(null)
const editingThread = ref(false)
const editForm = ref({ name: '', topic: '', description: '' })

const datasetMap = computed(() => {
  const map = new Map<string, DatasetRecord>()
  for (const dataset of project.value?.datasets ?? []) {
    map.set(dataset.id, dataset)
  }
  return map
})

const taskMap = computed(() => {
  const map = new Map<string, TaskSnapshot>()
  for (const task of project.value?.tasks ?? []) {
    map.set(task.id, task)
  }
  return map
})

const screeningRounds = computed(() =>
  (project.value?.tasks ?? [])
    .filter((task) => task.kind === 'screening')
    .sort((left, right) => dayjs(left.created_at).valueOf() - dayjs(right.created_at).valueOf())
)

const reportTasks = computed(() =>
  (project.value?.tasks ?? [])
    .filter((task) => task.kind === 'report')
    .sort((left, right) => dayjs(left.created_at).valueOf() - dayjs(right.created_at).valueOf())
)

const sortedTasks = computed(() =>
  [...(project.value?.tasks ?? [])].sort((left, right) => dayjs(left.created_at).valueOf() - dayjs(right.created_at).valueOf())
)

const cumulativeIncludedDataset = computed(() =>
  (project.value?.datasets ?? []).find((dataset) => dataset.kind === 'cumulative_included') ?? null
)

const latestSucceededScreening = computed(() =>
  [...screeningRounds.value].reverse().find((task) => task.status === 'succeeded') ?? null
)

const latestUnusedDataset = computed(() => {
  const task = latestSucceededScreening.value
  if (!task) return null
  return task.output_dataset_ids
    .map((datasetId) => datasetMap.value.get(datasetId) ?? null)
    .find((dataset) => dataset?.kind === 'unused') ?? null
})

const quickReportDatasetOptions = computed(() => {
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
  for (const round of [...screeningRounds.value].reverse()) {
    const includedDataset =
      round.output_dataset_ids
        .map((datasetId) => datasetMap.value.get(datasetId) ?? null)
        .find((dataset) => dataset?.kind === 'included') ?? null
    pushOnce(includedDataset, `第 ${screeningRounds.value.findIndex((item) => item.id === round.id) + 1} 轮纳入`)
  }
  return options
})

function friendlyDatasetLabel(dataset: DatasetRecord | null | undefined) {
  if (!dataset) return '未知来源'
  switch (dataset.kind) {
    case 'included':
      return '本轮纳入文献'
    case 'excluded':
      return '本轮剔除文献'
    case 'unused':
      return '本轮未使用文献'
    case 'cumulative_included':
      return '项目累计纳入文献'
    case 'included_reviewed':
      return '人工修正后的纳入文献'
    case 'excluded_reviewed':
      return '人工修正后的剔除文献'
    default:
      return dataset.label
  }
}

function sourceLabelOf(task: TaskSnapshot) {
  if (task.input_dataset_ids.length) {
    const labels = task.input_dataset_ids
      .map((datasetId) => friendlyDatasetLabel(datasetMap.value.get(datasetId)))
      .filter(Boolean)
    if (labels.length) return `延续自 ${labels.join(' + ')}`
  }
  if (task.parent_task_id && taskMap.value.get(task.parent_task_id)) {
    return `延续自上一轮：${taskMap.value.get(task.parent_task_id)?.title}`
  }
  if (task.kind === 'report') return '基于当前线程内的筛选结果生成报告'
  return '从新上传的文献开始这一轮筛选'
}

function firstLine(text: string | null | undefined) {
  return (text ?? '').split('\n')[0]?.trim() ?? ''
}

function screeningMetrics(task: TaskSnapshot): ThreadMetric[] {
  const summary = task.summary ?? {}
  const metrics: ThreadMetric[] = []
  if (summary.raw_entries_count !== undefined) metrics.push({ label: '原始', value: Number(summary.raw_entries_count) || 0 })
  if (summary.deduped_entries_count !== undefined) metrics.push({ label: '去重后', value: Number(summary.deduped_entries_count) || 0 })
  if (summary.included_count !== undefined) metrics.push({ label: '纳入', value: Number(summary.included_count) || 0 })
  if (summary.excluded_count !== undefined) metrics.push({ label: '剔除', value: Number(summary.excluded_count) || 0 })
  if (summary.uncertain_count !== undefined) metrics.push({ label: '不确定', value: Number(summary.uncertain_count) || 0 })
  if (summary.unused_count !== undefined) metrics.push({ label: '未使用', value: Number(summary.unused_count) || 0 })
  return metrics
}

function artifactByKey(task: TaskSnapshot, key: string) {
  return task.artifacts.find((artifact) => artifact.key === key) ?? null
}

function buildScreeningActions(task: TaskSnapshot): ThreadAction[] {
  const actions: ThreadAction[] = [
    {
      id: `${task.id}-detail`,
      label: '查看本轮详情',
      kind: 'route',
      to: `/tasks/${task.id}`,
      emphasis: 'ghost'
    }
  ]

  const includedArtifact = artifactByKey(task, 'included_ris') ?? artifactByKey(task, 'reviewed_included_ris')
  if (includedArtifact) {
    actions.push({
      id: `${task.id}-download-included`,
      label: '下载纳入 RIS',
      kind: 'download',
      href: getArtifactUrl(task.id, includedArtifact.key),
      emphasis: 'ghost'
    })
  }

  const unusedDataset = task.output_dataset_ids
    .map((datasetId) => datasetMap.value.get(datasetId) ?? null)
    .find((dataset) => dataset?.kind === 'unused') ?? null
  if (unusedDataset) {
    actions.push({
      id: `${task.id}-continue-unused`,
      label: '继续筛选未使用文献',
      kind: 'route',
      to: `/screening/new?projectId=${projectId.value}&sourceDatasetId=${unusedDataset.id}&parentTaskId=${task.id}`,
      emphasis: 'primary'
    })
  }

  const includedDataset = task.output_dataset_ids
    .map((datasetId) => datasetMap.value.get(datasetId) ?? null)
    .find((dataset) => dataset?.kind === 'included') ?? null
  if (includedDataset) {
    actions.push({
      id: `${task.id}-report`,
      label: '基于本轮纳入生成报告',
      kind: 'route',
      to: `/threads/${projectId.value}?reportDatasetId=${includedDataset.id}`,
      emphasis: 'secondary'
    })
  }
  return actions
}

function buildReportActions(task: TaskSnapshot): ThreadAction[] {
  const actions: ThreadAction[] = [
    {
      id: `${task.id}-detail`,
      label: '查看报告详情',
      kind: 'route',
      to: `/tasks/${task.id}`,
      emphasis: 'ghost'
    }
  ]
  const reportArtifact =
    artifactByKey(task, 'literature_report_reviewed') ??
    artifactByKey(task, 'literature_report')
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
  if (task.kind === 'screening') {
    const summary = task.summary ?? {}
    const included = Number(summary.included_count ?? 0)
    const excluded = Number(summary.excluded_count ?? 0)
    const uncertain = Number(summary.uncertain_count ?? 0)
    const unused = Number(summary.unused_count ?? 0)
    const body =
      task.status === 'succeeded'
        ? `这一轮初筛已完成。纳入 ${included} 篇，剔除 ${excluded} 篇，不确定 ${uncertain} 篇，未使用 ${unused} 篇。`
        : task.status === 'failed'
          ? `这一轮执行失败。${firstLine(task.error) || task.progress_message || '请进入详情页查看错误并继续执行。'}`
          : task.progress_message || '正在执行这一轮初筛。'

    return {
      id: task.id,
      taskId: task.id,
      kind: task.kind,
      status: task.status,
      title: task.title,
      eyebrow: 'Screening Round',
      body,
      sourceLabel: sourceLabelOf(task),
      note: task.status === 'failed' ? '失败后可以从详情页继续执行，不需要重新建主题。' : undefined,
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

  const referenceStyle = String(task.summary?.reference_style ?? 'gbt7714').toUpperCase()
  return {
    id: task.id,
    taskId: task.id,
    kind: task.kind,
    status: task.status,
    title: task.title,
    eyebrow: 'Report Task',
    body:
      task.status === 'succeeded'
        ? `报告已生成。当前参考样式为 ${referenceStyle}，你可以继续修正参考列表，或直接下载报告。`
        : task.status === 'failed'
          ? `报告生成失败。${firstLine(task.error) || task.progress_message || '请进入详情页查看错误并继续执行。'}`
          : task.progress_message || '正在整理逐篇总结、总体概览和参考列表。'
    ,
    sourceLabel: sourceLabelOf(task),
    note: task.status === 'succeeded' ? '如果参考列表不完整，可以在详情页粘贴修正后的版本并自动重排。' : undefined,
    createdAt: task.created_at,
    updatedAt: task.updated_at,
    phaseLabel: task.phase_label,
    progressCurrent: task.progress_current,
    progressTotal: task.progress_total,
    progressMessage: task.progress_message,
    metrics: [{ label: '样式', value: referenceStyle }],
    actions: buildReportActions(task)
  }
}

const threadMessages = computed(() => sortedTasks.value.map(buildThreadMessage))

const threadStats = computed(() => ({
  rounds: screeningRounds.value.length,
  reports: reportTasks.value.length,
  cumulativeIncluded: cumulativeIncludedDataset.value?.record_count ?? 0,
  running: sortedTasks.value.filter((task) => task.status === 'running' || task.status === 'pending').length
}))

function initializeReportDefaults() {
  if (!project.value) return
  reportTitle.value = `${project.value.name}-report`
  reportTopic.value = project.value.topic
  reportName.value = 'simple_report'
  reportReferenceStyle.value = 'gbt7714'
  if (cumulativeIncludedDataset.value) {
    reportDatasetIds.value = [cumulativeIncludedDataset.value.id]
  } else if (quickReportDatasetOptions.value.length) {
    reportDatasetIds.value = [quickReportDatasetOptions.value[0].value]
  } else {
    reportDatasetIds.value = []
  }
}

function openEditThread() {
  if (!project.value) return
  editForm.value = {
    name: project.value.name,
    topic: project.value.topic,
    description: project.value.description ?? ''
  }
  editingThread.value = true
}

async function saveThreadEdit() {
  if (!project.value) return
  if (!editForm.value.name.trim() || !editForm.value.topic.trim()) {
    message.warning('Thread name and topic are required')
    return
  }
  await projectsStore.updateProject(project.value.id, {
    name: editForm.value.name.trim(),
    topic: editForm.value.topic.trim(),
    description: editForm.value.description.trim()
  })
  editingThread.value = false
  message.success('Thread updated')
}

async function removeThread() {
  if (!project.value) return
  if (!window.confirm(`Delete thread "${project.value.name}"? This will also remove related screening and report tasks.`)) {
    return
  }
  const deletedProjectId = project.value.id
  await projectsStore.deleteProject(deletedProjectId)
  await tasksStore.refreshList()
  message.success('Thread deleted')
  await router.push('/')
}

watch(projectId, async (nextProjectId) => {
  if (!nextProjectId) return
  await tasksStore.refreshList()
  await projectsStore.loadProject(nextProjectId)
  initializeReportDefaults()
}, { immediate: true })

watch(
  () => route.query.reportDatasetId,
  (datasetId) => {
    if (typeof datasetId === 'string' && quickReportDatasetOptions.value.some((item) => item.value === datasetId)) {
      reportDatasetIds.value = [datasetId]
    }
  },
  { immediate: true }
)

async function submitThreadReport() {
  if (!project.value || !reportDatasetIds.value.length) {
    message.warning('先选择一组可用于报告的纳入结果')
    return
  }
  const preset = metaStore.providerPresets.find((item) => item.provider === 'deepseek') ?? metaStore.providerPresets[0]
  const task = await tasksStore.submitReport({
    title: reportTitle.value.trim() || `${project.value.name}-report`,
    screening_task_id: null,
    dataset_ids: reportDatasetIds.value,
    project_topic: reportTopic.value.trim() || project.value.topic,
    report_name: reportName.value.trim() || 'simple_report',
    retry_times: 6,
    timeout_seconds: 240,
    reference_style: reportReferenceStyle.value,
    model: {
      provider: preset.provider,
      model_name: preset.defaultModel,
      api_base_url: preset.defaultBaseUrl,
      api_key_env: preset.defaultApiKeyEnv,
      api_key: draftsStore.getProviderApiKey(preset.provider),
      temperature: 0,
      max_tokens: 1536,
      min_request_interval_seconds: 2
    }
  })
  message.success('报告任务已创建')
  await router.push(`/tasks/${task.id}`)
}

function startProjectPolling() {
  if (typeof window === 'undefined' || pollTimer.value !== null) return
  pollTimer.value = window.setInterval(async () => {
    await Promise.all([tasksStore.refreshList(), projectsStore.loadProject(projectId.value)])
  }, 4000)
}

function stopProjectPolling() {
  if (pollTimer.value !== null && typeof window !== 'undefined') {
    window.clearInterval(pollTimer.value)
  }
  pollTimer.value = null
}

onMounted(async () => {
  draftsStore.hydrate()
  await metaStore.ensureLoaded()
  await Promise.all([tasksStore.refreshList(), projectsStore.loadProject(projectId.value)])
  initializeReportDefaults()
})

watch(
  () => sortedTasks.value.some((task) => task.status === 'running' || task.status === 'pending'),
  (hasRunning) => {
    if (hasRunning) startProjectPolling()
    else stopProjectPolling()
  },
  { immediate: true }
)

onUnmounted(() => {
  stopProjectPolling()
})
</script>

<template>
  <div v-if="project" class="thread-view">
    <section class="thread-hero panel-surface">
      <div>
        <div class="eyebrow">Topic Thread</div>
        <h1>{{ project.name }}</h1>
        <p>{{ project.topic }}</p>
      </div>
      <NSpace>
        <NButton quaternary @click="openEditThread">
          <template #icon>
            <Pencil :size="16" />
          </template>
          Edit Thread
        </NButton>
        <NButton quaternary @click="removeThread">
          <template #icon>
            <Trash2 :size="16" />
          </template>
          Delete Thread
        </NButton>
        <RouterLink :to="{ path: '/screening/new', query: { projectId: project.id } }">
          <NButton type="primary">
            <template #icon>
              <GitBranchPlus :size="16" />
            </template>
            开始新一轮筛选
          </NButton>
        </RouterLink>
        <NButton tertiary @click="projectsStore.loadProject(project.id)">
          <template #icon>
            <RefreshCw :size="16" />
          </template>
          刷新线程
        </NButton>
      </NSpace>
    </section>

    <section class="thread-metrics">
      <OverviewMetric label="初筛轮次" :value="threadStats.rounds" />
      <OverviewMetric label="报告任务" :value="threadStats.reports" />
      <OverviewMetric label="累计纳入" :value="threadStats.cumulativeIncluded" />
      <OverviewMetric label="运行中" :value="threadStats.running" />
    </section>

    <div class="thread-layout">
      <section class="thread-stream">
        <NCard class="panel-surface intro-card" embedded>
          <div class="intro-eyebrow">Thread Context</div>
          <div class="intro-title">这个主题里的所有筛选轮次和报告都会按时间顺序沉淀在这里。</div>
          <div class="intro-copy">
            你不需要再管理 dataset。只需要看每一轮留下了什么结果，以及下一步是“继续筛选未使用文献”还是“基于当前纳入生成报告”。
          </div>
        </NCard>

        <div v-if="threadMessages.length" class="message-stack">
          <ThreadMessageCard
            v-for="messageItem in threadMessages"
            :key="messageItem.id"
            :message="messageItem"
          />
        </div>
        <NEmpty v-else class="panel-surface empty-thread" description="当前线程还没有任何轮次。先发起首轮初筛。" />
      </section>

      <aside class="thread-side">
        <NCard title="继续这个主题" class="panel-surface">
          <div class="quick-action-stack">
            <RouterLink :to="{ path: '/screening/new', query: { projectId: project.id } }">
              <NButton type="primary" block>
                <template #icon>
                  <FileSearch :size="16" />
                </template>
                上传新文献并开始下一轮
              </NButton>
            </RouterLink>

            <RouterLink
              v-if="latestUnusedDataset && latestSucceededScreening"
              :to="{
                path: '/screening/new',
                query: {
                  projectId: project.id,
                  sourceDatasetId: latestUnusedDataset.id,
                  parentTaskId: latestSucceededScreening.id
                }
              }"
            >
              <NButton secondary type="success" block>
                <template #icon>
                  <GitBranchPlus :size="16" />
                </template>
                从最近一轮未使用文献继续筛选
              </NButton>
            </RouterLink>

            <RouterLink v-if="latestSucceededScreening" :to="`/tasks/${latestSucceededScreening.id}`">
              <NButton tertiary block>进入最近一轮做人工复核</NButton>
            </RouterLink>
          </div>
          <NAlert v-if="!latestUnusedDataset" type="info" :show-icon="false" class="side-note">
            最近一轮还没有可继续使用的“未使用文献”。先完成一轮初筛，或直接上传新文献开始下一轮。
          </NAlert>
        </NCard>

        <NCard title="在线生成报告" class="panel-surface">
          <NForm label-placement="top">
            <NFormItem label="报告任务名称">
              <NInput v-model:value="reportTitle" placeholder="例如：猫咪交互文献整理报告" />
            </NFormItem>
            <NFormItem label="报告主题">
              <NInput v-model:value="reportTopic" type="textarea" :autosize="{ minRows: 3, maxRows: 5 }" />
            </NFormItem>
            <NFormItem label="报告来源">
              <NSelect v-model:value="reportDatasetIds" multiple :options="quickReportDatasetOptions" />
            </NFormItem>
            <NFormItem label="参考样式">
              <NSelect
                v-model:value="reportReferenceStyle"
                :options="metaStore.referenceStyles.map((item) => ({ label: item.label, value: item.value }))"
              />
            </NFormItem>
            <NFormItem label="输出目录名">
              <NInput v-model:value="reportName" placeholder="simple_report" />
            </NFormItem>
          </NForm>
          <NButton type="primary" block :disabled="!reportDatasetIds.length" @click="submitThreadReport">
            <template #icon>
              <WandSparkles :size="16" />
            </template>
            基于选中结果生成报告
          </NButton>
        </NCard>

        <NCard title="线程概览" class="panel-surface">
          <div class="summary-list">
            <div class="summary-row">
              <span>最近更新</span>
              <strong>{{ dayjs(project.updated_at).format('YYYY-MM-DD HH:mm') }}</strong>
            </div>
            <div class="summary-row">
              <span>最近成功轮次</span>
              <strong>{{ latestSucceededScreening?.title ?? '暂无' }}</strong>
            </div>
            <div class="summary-row">
              <span>累计纳入文件</span>
              <strong>{{ cumulativeIncludedDataset ? `${cumulativeIncludedDataset.record_count ?? 0} 篇` : '暂无' }}</strong>
            </div>
          </div>
        </NCard>
      </aside>
    </div>

    <NModal v-model:show="editingThread" preset="card" style="max-width: 640px" title="Edit Thread">
      <NForm label-placement="top">
        <NFormItem label="Thread Name">
          <NInput v-model:value="editForm.name" />
        </NFormItem>
        <NFormItem label="Topic">
          <NInput v-model:value="editForm.topic" type="textarea" :autosize="{ minRows: 3, maxRows: 6 }" />
        </NFormItem>
        <NFormItem label="Description">
          <NInput v-model:value="editForm.description" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="editingThread = false">Cancel</NButton>
          <NButton type="primary" @click="saveThreadEdit">Save</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.thread-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.thread-hero {
  padding: 24px;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
}

.eyebrow,
.intro-eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 12px;
  color: #6a776c;
}

h1 {
  margin: 8px 0 10px;
}

p {
  margin: 0;
  color: #526055;
  line-height: 1.7;
}

.thread-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.thread-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(320px, 0.95fr);
  gap: 18px;
  align-items: start;
}

.thread-stream,
.thread-side {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.thread-side {
  position: sticky;
  top: 22px;
}

.intro-card {
  padding: 18px;
}

.intro-title {
  margin-top: 8px;
  font-size: 20px;
  font-weight: 700;
}

.intro-copy {
  margin-top: 10px;
  color: #526055;
  line-height: 1.75;
}

.message-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.quick-action-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.side-note {
  margin-top: 14px;
}

.summary-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  color: #516055;
}

.empty-thread {
  padding: 30px;
}

@media (max-width: 1200px) {
  .thread-layout,
  .thread-metrics {
    grid-template-columns: 1fr;
  }

  .thread-side {
    position: static;
  }
}

@media (max-width: 860px) {
  .thread-hero {
    flex-direction: column;
  }
}
</style>
