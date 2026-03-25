<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
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
import type { DatasetRecord, TaskSnapshot } from '@/types/api'
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
const editingThread = ref(false)
const editForm = ref({ name: '', topic: '', description: '' })
const pollTimer = ref<number | null>(null)
const reportPanelRef = ref<HTMLElement | null>(null)
const reportFocusNote = ref('')
const reportPanelHighlighted = ref(false)
let reportFocusTimer: number | null = null

const datasetMap = computed(() => {
  const map = new Map<string, DatasetRecord>()
  for (const dataset of project.value?.datasets ?? []) {
    map.set(dataset.id, dataset)
  }
  return map
})

const tasks = computed(() => [...(project.value?.tasks ?? [])].sort((a, b) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf()))
const strategyTasks = computed(() => tasks.value.filter((task) => task.kind === 'strategy'))
const screeningRounds = computed(() => tasks.value.filter((task) => task.kind === 'screening'))
const reportTasks = computed(() => tasks.value.filter((task) => task.kind === 'report'))

const cumulativeIncludedDataset = computed(() =>
  (project.value?.datasets ?? []).find((dataset) => dataset.kind === 'cumulative_included') ?? null
)
const fulltextReadyDataset = computed(() =>
  (project.value?.datasets ?? []).find((dataset) => dataset.kind === 'fulltext_ready') ?? null
)

const latestSucceededScreening = computed(() => [...screeningRounds.value].reverse().find((task) => task.status === 'succeeded') ?? null)

function latestMatchingDataset(task: TaskSnapshot, kinds: string[]) {
  const matches = task.output_dataset_ids
    .map((datasetId) => datasetMap.value.get(datasetId) ?? null)
    .filter((dataset): dataset is DatasetRecord => Boolean(dataset && kinds.includes(dataset.kind)))
  return matches.length ? matches[matches.length - 1] : null
}

const latestUnusedDataset = computed(() => {
  const task = latestSucceededScreening.value
  if (!task) return null
  return latestMatchingDataset(task, ['unused'])
})

function friendlyDatasetLabel(dataset: DatasetRecord | null | undefined) {
  if (!dataset) return '未知来源'
  switch (dataset.kind) {
    case 'included':
      return '本轮纳入文献'
    case 'included_reviewed':
      return '人工复核后纳入文献'
    case 'excluded':
      return '本轮剔除文献'
    case 'excluded_reviewed':
      return '人工复核后剔除文献'
    case 'unused':
      return '本轮未使用文献'
    case 'cumulative_included':
      return '项目累计纳入'
    case 'fulltext_ready':
      return '仅已获取全文'
    default:
      return dataset.label
  }
}

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
    const includedDataset = latestMatchingDataset(round, ['included_reviewed', 'included'])
    pushOnce(includedDataset, `第 ${screeningRounds.value.findIndex((item) => item.id === round.id) + 1} 轮纳入`)
  }
  return options
})

const reportDatasetOptions = computed(() => {
  const options: Array<{ label: string; value: string }> = []
  if (fulltextReadyDataset.value && (fulltextReadyDataset.value.record_count ?? 0) > 0) {
    options.push({
      label: `仅已获取全文 · ${fulltextReadyDataset.value.record_count ?? '-'} 篇`,
      value: fulltextReadyDataset.value.id
    })
  }
  for (const option of quickReportDatasetOptions.value) {
    if (!options.some((item) => item.value === option.value)) {
      options.push(option)
    }
  }
  return options
})

const fulltextCounts = computed(() => {
  const counts = { pending: 0, ready: 0, unavailable: 0, deferred: 0 }
  for (const item of project.value?.fulltext_queue ?? []) counts[item.status] += 1
  return counts
})

const threadStats = computed(() => ({
  strategies: strategyTasks.value.length,
  rounds: screeningRounds.value.length,
  reports: reportTasks.value.length,
  cumulativeIncluded: cumulativeIncludedDataset.value?.record_count ?? 0,
  running: tasks.value.filter((task) => task.status === 'running' || task.status === 'pending').length
}))

function sourceLabelOf(task: TaskSnapshot) {
  if (task.input_dataset_ids.length) {
    const labels = task.input_dataset_ids
      .map((datasetId) => friendlyDatasetLabel(datasetMap.value.get(datasetId)))
      .filter(Boolean)
    if (labels.length) return `来源：${labels.join(' + ')}`
  }
  if (task.parent_task_id) return '来源：延续上一轮'
  if (task.kind === 'report') return '来源：选中的报告来源集合'
  if (task.kind === 'strategy') return '来源：研究需求生成检索与筛选方案'
  return '来源：新上传文献'
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

function buildStrategyActions(task: TaskSnapshot): ThreadAction[] {
  const actions: ThreadAction[] = [
    { id: `${task.id}-detail`, label: '查看方案详情', kind: 'route', to: `/tasks/${task.id}`, emphasis: 'ghost' }
  ]
  const markdownArtifact = artifactByKey(task, 'strategy_plan')
  if (markdownArtifact) {
    actions.push({
      id: `${task.id}-download-markdown`,
      label: '下载方案 Markdown',
      kind: 'download',
      href: getArtifactUrl(task.id, markdownArtifact.key),
      emphasis: 'ghost'
    })
  }
  actions.push({
    id: `${task.id}-screening`,
    label: '带入初筛',
    kind: 'route',
    to: `/screening/new?projectId=${projectId.value}&strategyTaskId=${task.id}`,
    emphasis: 'primary'
  })
  return actions
}

function buildScreeningActions(task: TaskSnapshot): ThreadAction[] {
  const actions: ThreadAction[] = [
    { id: `${task.id}-detail`, label: '查看本轮详情', kind: 'route', to: `/tasks/${task.id}`, emphasis: 'ghost' }
  ]
  const includedArtifact = artifactByKey(task, 'reviewed_included_ris') ?? artifactByKey(task, 'included_ris')
  if (includedArtifact) {
    actions.push({
      id: `${task.id}-download-included`,
      label: '下载纳入 RIS',
      kind: 'download',
      href: getArtifactUrl(task.id, includedArtifact.key),
      emphasis: 'ghost'
    })
  }
  const unusedDataset = latestMatchingDataset(task, ['unused'])
  if (unusedDataset) {
    actions.push({
      id: `${task.id}-continue-unused`,
      label: '继续筛选未使用文献',
      kind: 'route',
      to: `/screening/new?projectId=${projectId.value}&sourceDatasetId=${unusedDataset.id}&parentTaskId=${task.id}`,
      emphasis: 'primary'
    })
  }
  const includedDataset = latestMatchingDataset(task, ['included_reviewed', 'included'])
  if (includedDataset) {
    actions.push({
      id: `${task.id}-fulltext`,
      label: '进入全文获取',
      kind: 'route',
      to: `/threads/${projectId.value}/fulltext`,
      emphasis: 'secondary'
    })
    actions.push({
      id: `${task.id}-report`,
      label: '带入报告工作台',
      kind: 'route',
      to: `/threads/${projectId.value}?reportDatasetId=${includedDataset.id}&focusPanel=report`,
      emphasis: 'report'
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
    const summary = task.summary ?? {}
    const databaseCount = Number(summary.database_count ?? 0)
    const body =
      task.status === 'succeeded'
        ? '检索与筛选方案已生成。可以直接带入初筛。'
        : task.status === 'failed'
          ? `方案生成失败。${firstLine(task.error) || task.progress_message || '请进入详情页查看错误。'}`
          : task.progress_message || '正在生成检索与筛选方案。'
    return {
      id: task.id,
      taskId: task.id,
      kind: task.kind,
      status: task.status,
      title: task.title,
      eyebrow: 'Strategy Task',
      body,
      sourceLabel: sourceLabelOf(task),
      note: task.status === 'succeeded' ? '方案结果会保存在当前主题中，可直接带入初筛。' : undefined,
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
    const body =
      task.status === 'succeeded'
        ? `本轮初筛完成。纳入 ${Number(summary.included_count ?? 0)} 篇，剔除 ${Number(summary.excluded_count ?? 0)} 篇，不确定 ${Number(summary.uncertain_count ?? 0)} 篇，未使用 ${Number(summary.unused_count ?? 0)} 篇。`
        : task.status === 'failed'
          ? `本轮执行失败。${firstLine(task.error) || task.progress_message || '请进入详情页查看错误。'}`
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
      note: task.status === 'failed' ? '失败后可以在详情页继续执行。' : undefined,
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
        ? `报告已生成。当前参考样式为 ${referenceStyle}。`
        : task.status === 'failed'
          ? `报告生成失败。${firstLine(task.error) || task.progress_message || '请进入详情页查看错误。'}`
          : task.progress_message || '正在生成报告。',
    sourceLabel: sourceLabelOf(task),
    note: task.status === 'succeeded' ? '如果参考列表不完整，可在报告详情页粘贴修正版自动重排。' : undefined,
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

const threadMessages = computed(() => tasks.value.map(buildThreadMessage))

function initializeReportDefaults() {
  if (!project.value) return
  reportTitle.value = `${project.value.name}-report`
  reportTopic.value = project.value.topic
  reportName.value = 'simple_report'
  reportReferenceStyle.value = 'gbt7714'
  if (fulltextReadyDataset.value && (fulltextReadyDataset.value.record_count ?? 0) > 0) {
    reportDatasetIds.value = [fulltextReadyDataset.value.id]
  } else if (cumulativeIncludedDataset.value) {
    reportDatasetIds.value = [cumulativeIncludedDataset.value.id]
  } else if (reportDatasetOptions.value.length) {
    reportDatasetIds.value = [reportDatasetOptions.value[0].value]
  } else {
    reportDatasetIds.value = []
  }
}

function openEditThread() {
  if (!project.value) return
  editForm.value = {
    name: project.value.name,
    topic: project.value.topic,
    description: project.value.description
  }
  editingThread.value = true
}

async function saveThreadEdits() {
  if (!project.value) return
  await projectsStore.updateProject(project.value.id, {
    name: editForm.value.name.trim() || project.value.name,
    topic: editForm.value.topic.trim() || project.value.topic,
    description: editForm.value.description.trim()
  })
  editingThread.value = false
  message.success('主题已更新')
}

async function removeThread() {
  if (!project.value) return
  const currentId = project.value.id
  await projectsStore.deleteProject(currentId)
  message.success('主题已删除')
  await router.push('/')
}

watch(projectId, async (nextProjectId) => {
  if (!nextProjectId) return
  reportDatasetIds.value = []
  await tasksStore.refreshList()
  await projectsStore.loadProject(nextProjectId)
  initializeReportDefaults()
}, { immediate: true })

watch(
  () => route.query.reportDatasetId,
  (datasetId) => {
    if (typeof datasetId === 'string' && reportDatasetOptions.value.some((item) => item.value === datasetId)) {
      reportDatasetIds.value = [datasetId]
    }
  },
  { immediate: true }
)

watch(
  [() => route.query.reportDatasetId, () => route.query.focusPanel, reportDatasetOptions],
  async ([datasetId, focusPanel, options]) => {
    if (focusPanel !== 'report' || typeof datasetId !== 'string') {
      reportFocusNote.value = ''
      reportPanelHighlighted.value = false
      return
    }
    if (!options.some((item) => item.value === datasetId)) return
    reportFocusNote.value = '已为你带入当前轮次的纳入结果。下一步只需要确认报告主题和参考样式，然后点击生成。'
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

watch(reportDatasetOptions, (options) => {
  const validIds = new Set(options.map((item) => item.value))
  const nextIds = reportDatasetIds.value.filter((datasetId) => validIds.has(datasetId))
  if (nextIds.length !== reportDatasetIds.value.length) {
    reportDatasetIds.value = nextIds
  }
  if (!reportDatasetIds.value.length && options.length) {
    reportDatasetIds.value = [options[0].value]
  }
}, { deep: true })

async function submitThreadReport() {
  if (!project.value || !reportDatasetIds.value.length) {
    message.warning('先选择一组可用于报告的纳入结果')
    return
  }
  const validIds = new Set(reportDatasetOptions.value.map((item) => item.value))
  const selectedIds = reportDatasetIds.value.filter((datasetId) => validIds.has(datasetId))
  if (!selectedIds.length) {
    message.warning('当前选择的报告来源已失效，请重新选择后再生成报告')
    if (reportDatasetOptions.value.length) {
      reportDatasetIds.value = [reportDatasetOptions.value[0].value]
    }
    return
  }
  const preset = metaStore.providerPresets.find((item) => item.provider === 'deepseek') ?? metaStore.providerPresets[0]
  try {
    const task = await tasksStore.submitReport({
      title: reportTitle.value.trim() || `${project.value.name}-report`,
      project_id: project.value.id,
      screening_task_id: null,
      dataset_ids: selectedIds,
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
  } catch (error: any) {
    const detail = error?.response?.data?.detail
    message.error(typeof detail === 'string' && detail ? detail : '报告创建失败，请检查报告来源后重试')
  }
}

function startProjectPolling() {
  if (typeof window === 'undefined' || pollTimer.value !== null) return
  pollTimer.value = window.setInterval(async () => {
    if (!project.value) return
    await Promise.all([tasksStore.refreshList(), projectsStore.loadProject(project.value.id)])
    initializeReportDefaults()
  }, 4000)
}

function stopProjectPolling() {
  if (pollTimer.value !== null && typeof window !== 'undefined') {
    window.clearInterval(pollTimer.value)
  }
  pollTimer.value = null
}

onMounted(async () => {
  await metaStore.ensureLoaded()
  await Promise.all([tasksStore.refreshList(), projectsStore.loadProject(projectId.value)])
  initializeReportDefaults()
})

watch(
  () => tasks.value.some((task) => task.status === 'running' || task.status === 'pending'),
  (hasRunning) => {
    if (hasRunning) startProjectPolling()
    else stopProjectPolling()
  },
  { immediate: true }
)

onUnmounted(() => {
  stopProjectPolling()
  if (reportFocusTimer !== null && typeof window !== 'undefined') {
    window.clearTimeout(reportFocusTimer)
  }
})
</script>

<template>
  <div v-if="project" class="thread-view">
    <section class="thread-hero">
      <div class="thread-hero-copy">
        <div class="eyebrow">Topic Thread</div>
        <h1>{{ project.name }}</h1>
        <p>{{ project.topic }}</p>
      </div>
      <NSpace class="thread-hero-actions">
        <NButton secondary @click="openEditThread">
          <template #icon><Pencil :size="16" /></template>
          Edit Thread
        </NButton>
        <NButton tertiary @click="removeThread">
          <template #icon><Trash2 :size="16" /></template>
          Delete Thread
        </NButton>
        <RouterLink :to="{ path: '/strategy/new', query: { projectId: project.id } }">
          <NButton secondary>
            <template #icon><WandSparkles :size="16" /></template>
            生成检索与筛选方案
          </NButton>
        </RouterLink>
        <RouterLink :to="{ path: '/screening/new', query: { projectId: project.id } }">
          <NButton type="primary">
            <template #icon><GitBranchPlus :size="16" /></template>
            开始新一轮筛选
          </NButton>
        </RouterLink>
        <NButton tertiary @click="projectsStore.loadProject(project.id)">
          <template #icon><RefreshCw :size="16" /></template>
          刷新主题
        </NButton>
      </NSpace>
    </section>

    <section class="thread-metrics">
      <OverviewMetric label="策略任务" :value="threadStats.strategies" />
      <OverviewMetric label="初筛轮次" :value="threadStats.rounds" />
      <OverviewMetric label="报告任务" :value="threadStats.reports" />
      <OverviewMetric label="累计纳入" :value="threadStats.cumulativeIncluded" />
      <OverviewMetric label="运行中" :value="threadStats.running" />
    </section>

    <div class="thread-layout">
      <section class="thread-stream">
        <NCard class="panel-surface intro-card" embedded>
          <div class="intro-eyebrow">Thread Context</div>
          <div class="intro-title">这个主题里的筛选轮次、全文获取与报告都会按时间顺序沉淀在这里。</div>
          <div class="intro-copy">只需要关心每一轮留下了什么结果，以及下一步是继续筛选、做全文获取，还是基于当前结果生成报告。</div>
        </NCard>

        <div v-if="threadMessages.length" class="message-stack">
          <ThreadMessageCard v-for="messageItem in threadMessages" :key="messageItem.id" :message="messageItem" />
        </div>
        <NEmpty v-else class="panel-surface empty-thread" description="当前主题还没有任何轮次。先发起首轮初筛。" />
      </section>

      <aside class="thread-side">
        <NCard title="继续这个主题" class="panel-surface">
          <div class="quick-action-stack">
            <RouterLink :to="{ path: '/strategy/new', query: { projectId: project.id } }">
              <NButton secondary type="primary" block>
                <template #icon><WandSparkles :size="16" /></template>
                先生成检索与筛选方案
              </NButton>
            </RouterLink>

            <RouterLink :to="{ path: '/screening/new', query: { projectId: project.id } }">
              <NButton type="primary" block>
                <template #icon><FileSearch :size="16" /></template>
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
              <NButton secondary block>
                <template #icon><GitBranchPlus :size="16" /></template>
                从最近一轮未使用文献继续筛选
              </NButton>
            </RouterLink>

            <RouterLink v-if="latestSucceededScreening" :to="`/tasks/${latestSucceededScreening.id}`">
              <NButton tertiary block>进入最近一轮做人工复核</NButton>
            </RouterLink>

            <RouterLink :to="`/threads/${project.id}/fulltext`">
              <NButton tertiary block>进入全文获取工作台</NButton>
            </RouterLink>
          </div>
          <NAlert v-if="!latestUnusedDataset" type="info" :show-icon="false" class="side-note">
            最近一轮还没有可继续使用的未使用文献。先完成一轮初筛，或直接上传新文献开始下一轮。
          </NAlert>
        </NCard>

        <NCard ref="reportPanelRef" title="报告工作台" class="panel-surface report-workspace-card" :class="{ highlighted: reportPanelHighlighted }">
          <NAlert v-if="reportFocusNote" type="warning" :show-icon="false" class="report-workspace-alert">
            {{ reportFocusNote }}
          </NAlert>
          <div class="report-workspace-copy">
            <span>这里是报告阶段，不是继续筛选。</span>
            <strong>当前会基于你选中的纳入结果或“仅已获取全文”来生成综述报告。</strong>
          </div>
          <div class="report-workspace-status">
            <NTag round type="warning">报告来源 {{ reportDatasetIds.length }} 组</NTag>
            <NTag v-if="fulltextReadyDataset && (fulltextReadyDataset.record_count ?? 0) > 0" round type="success">
              已获取全文 {{ fulltextReadyDataset.record_count ?? 0 }} 篇
            </NTag>
          </div>
          <NForm label-placement="top">
            <NFormItem label="报告任务名称">
              <NInput v-model:value="reportTitle" placeholder="例如：某主题文献整理报告" />
            </NFormItem>
            <NFormItem label="报告主题">
              <NInput v-model:value="reportTopic" type="textarea" :autosize="{ minRows: 3, maxRows: 5 }" />
            </NFormItem>
            <NFormItem label="报告来源">
              <NSelect v-model:value="reportDatasetIds" multiple :options="reportDatasetOptions" />
            </NFormItem>
            <NFormItem label="参考样式">
              <NSelect v-model:value="reportReferenceStyle" :options="metaStore.referenceStyles.map((item) => ({ label: item.label, value: item.value }))" />
            </NFormItem>
            <NFormItem label="输出目录名">
              <NInput v-model:value="reportName" placeholder="simple_report" />
            </NFormItem>
          </NForm>
          <NButton type="primary" block :disabled="!reportDatasetIds.length" @click="submitThreadReport">
            <template #icon><WandSparkles :size="16" /></template>
            基于选中结果生成报告
          </NButton>
        </NCard>

        <NCard title="全文获取工作台" class="panel-surface">
          <div class="fulltext-summary-card">
            <div class="fulltext-summary-copy">
              <strong>把全文标记、筛选和链接检查放到单独页面处理。</strong>
              <span>这里保留摘要和入口，避免和报告表单挤在同一块区域。</span>
            </div>
            <div class="fulltext-summary">
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext` }">
                <NTag round :bordered="false" class="summary-tag">全部 {{ project.fulltext_queue.length }}</NTag>
              </RouterLink>
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext`, query: { status: 'pending' } }">
                <NTag round :bordered="false" class="summary-tag">未处理 {{ fulltextCounts.pending }}</NTag>
              </RouterLink>
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext`, query: { status: 'ready' } }">
                <NTag round type="success" :bordered="false" class="summary-tag">已获取 {{ fulltextCounts.ready }}</NTag>
              </RouterLink>
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext`, query: { status: 'unavailable' } }">
                <NTag round type="error" :bordered="false" class="summary-tag">无权限 {{ fulltextCounts.unavailable }}</NTag>
              </RouterLink>
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext`, query: { status: 'deferred' } }">
                <NTag round type="warning" :bordered="false" class="summary-tag">暂缓 {{ fulltextCounts.deferred }}</NTag>
              </RouterLink>
            </div>
            <div class="fulltext-entry-actions">
              <RouterLink :to="`/threads/${project.id}/fulltext`">
                <NButton type="primary" block>打开全文获取页</NButton>
              </RouterLink>
              <RouterLink
                v-if="fulltextReadyDataset && (fulltextReadyDataset.record_count ?? 0) > 0"
                :to="{ path: `/threads/${project.id}`, query: { reportDatasetId: fulltextReadyDataset.id, focusPanel: 'report' } }"
              >
                <NButton secondary block>用已获取全文生成报告</NButton>
              </RouterLink>
            </div>
          </div>
        </NCard>

        <NCard title="主题概览" class="panel-surface">
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

    <NModal v-model:show="editingThread" preset="card" title="编辑主题" style="max-width: 720px">
      <NForm label-placement="top">
        <NFormItem label="主题名称">
          <NInput v-model:value="editForm.name" />
        </NFormItem>
        <NFormItem label="研究主题">
          <NInput v-model:value="editForm.topic" type="textarea" :autosize="{ minRows: 3, maxRows: 5 }" />
        </NFormItem>
        <NFormItem label="补充说明">
          <NInput v-model:value="editForm.description" type="textarea" :autosize="{ minRows: 4, maxRows: 8 }" />
        </NFormItem>
      </NForm>
      <template #action>
        <NSpace justify="end">
          <NButton @click="editingThread = false">取消</NButton>
          <NButton type="primary" @click="saveThreadEdits">保存</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
  <NEmpty v-else description="主题不存在或仍在加载中" class="panel-surface empty-thread" />
</template>

<style scoped>
.thread-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.thread-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px 24px;
  align-items: end;
  padding: 4px 0 2px;
  border-bottom: 1px solid rgba(90, 107, 93, 0.12);
}

.thread-hero-copy {
  min-width: 0;
}

.thread-hero-actions {
  justify-self: end;
  justify-content: flex-end;
}

.thread-hero h1 {
  margin: 8px 0 8px;
  font-size: 34px;
  line-height: 1.12;
}

.thread-hero p {
  margin: 0;
  color: #5e6d62;
  max-width: 860px;
  line-height: 1.6;
}

.thread-metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
}

.thread-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(320px, 0.95fr);
  gap: 18px;
}

.thread-stream,
.thread-side {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.intro-card {
  border-radius: 22px;
}

.intro-eyebrow,
.eyebrow {
  font-size: 12px;
  color: #6a776c;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.intro-title {
  margin-top: 8px;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.35;
}

.intro-copy {
  margin-top: 10px;
  color: #4d5c51;
  line-height: 1.7;
}

.message-stack,
.quick-action-stack,
.summary-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.side-note {
  margin-top: 14px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #506055;
}

.summary-row strong {
  color: #223126;
}

.report-workspace-card {
  border-color: rgba(196, 137, 29, 0.22);
  background: rgba(255, 250, 242, 0.9);
  transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
}

.report-workspace-card.highlighted {
  border-color: rgba(196, 137, 29, 0.46);
  box-shadow: 0 18px 40px rgba(196, 137, 29, 0.16);
  transform: translateY(-1px);
}

.report-workspace-alert {
  margin-bottom: 14px;
}

.report-workspace-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
  color: #665748;
}

.report-workspace-status {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.fulltext-summary-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.fulltext-summary-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #506055;
}

.fulltext-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.summary-tag {
  cursor: pointer;
}

.fulltext-entry-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-thread {
  min-height: 180px;
  display: grid;
  place-items: center;
}

@media (max-width: 1200px) {
  .thread-layout {
    grid-template-columns: 1fr;
  }

  .thread-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .thread-hero {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .thread-hero-actions {
    justify-self: start;
    justify-content: flex-start;
  }
}

@media (max-width: 720px) {
  .thread-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
