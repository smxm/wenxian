<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { BookOpenText, FileSearch, FileText, Pencil, Sparkles, Trash2 } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NDynamicInput,
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
import ThreadMessageCard from '@/components/ThreadMessageCard.vue'
import OverviewMetric from '@/components/OverviewMetric.vue'
import { getArtifactUrl } from '@/api/client'
import { useDraftsStore } from '@/stores/drafts'
import { useMetaStore } from '@/stores/meta'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import { buildCriteriaMarkdown } from '@/utils/strategy'
import type { DatasetRecord, StrategyDatabase, TaskSnapshot, ThreadProfile } from '@/types/api'
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
const editingThread = ref(false)
const editForm = ref({
  name: '',
  description: '',
  researchNeed: '',
  topic: '',
  inclusion: [''],
  exclusion: [''],
  selectedDatabases: ['scopus', 'wos', 'pubmed', 'cnki'] as StrategyDatabase[]
})
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
const latestStrategyTask = computed(() => [...strategyTasks.value].reverse()[0] ?? null)
const latestSucceededScreening = computed(() => [...screeningRounds.value].reverse().find((task) => task.status === 'succeeded') ?? null)

const screeningDefaults = computed(() => threadProfile.value?.screening ?? null)
const strategyContext = computed(() => threadProfile.value?.strategy ?? null)
const cumulativeIncludedDataset = computed(() =>
  (project.value?.datasets ?? []).find((dataset) => dataset.kind === 'cumulative_included') ?? null
)
const fulltextReadyDataset = computed(() =>
  (project.value?.datasets ?? []).find((dataset) => dataset.kind === 'fulltext_ready') ?? null
)

const fulltextCounts = computed(() => {
  const counts = { pending: 0, ready: 0, excluded: 0, unavailable: 0, deferred: 0 }
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

const stageCards = computed(() => [
  {
    title: '线程方案',
    description: strategyContext.value?.plan ? '已生成检索式、主题和标准' : '先生成线程主题与筛选标准',
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
    title: '统一复核',
    description: project.value?.fulltext_queue.length ? '在同一页处理筛选复核与全文状态' : '初筛完成后会自动汇入这里',
    value: fulltextCounts.value.ready,
    unit: '篇已获取',
    emphasis: fulltextCounts.value.ready ? 'ready' : 'pending'
  },
  {
    title: '生成报告',
    description: (fulltextReadyDataset.value?.record_count ?? 0) > 0 ? '可以基于已获取全文生成报告' : '先把需要的全文标记为已获取',
    value: fulltextReadyDataset.value?.record_count ?? 0,
    unit: '篇全文',
    emphasis: (fulltextReadyDataset.value?.record_count ?? 0) > 0 ? 'ready' : 'pending'
  }
])

function latestMatchingDataset(task: TaskSnapshot, kinds: string[]) {
  const matches = task.output_dataset_ids
    .map((datasetId) => datasetMap.value.get(datasetId) ?? null)
    .filter((dataset): dataset is DatasetRecord => Boolean(dataset && kinds.includes(dataset.kind)))
  return matches.length ? matches[matches.length - 1] : null
}

function sourceLabelOf(task: TaskSnapshot) {
  if (task.input_dataset_ids.length) {
    const labels = task.input_dataset_ids
      .map((datasetId) => datasetMap.value.get(datasetId)?.label ?? datasetId)
      .filter(Boolean)
    if (labels.length) return `来源：${labels.join(' + ')}`
  }
  if (task.parent_task_id) return '来源：延续上一轮'
  if (task.kind === 'report') return '来源：已获取全文'
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
      label: '进入统一复核',
      kind: 'route',
      to: `/threads/${projectId.value}/fulltext`,
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
      note: task.status === 'succeeded' ? '下一步建议去全文获取工作台确认需要保留的全文。' : undefined,
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
  reportTitle.value = `${project.value.name}-report`
  reportTopic.value = screeningDefaults.value?.topic || project.value.topic
  reportName.value = 'simple_report'
  reportReferenceStyle.value = 'gbt7714'
}

function openEditThread() {
  if (!project.value || !threadProfile.value) return
  editForm.value = {
    name: project.value.name,
    description: project.value.description ?? '',
    researchNeed: threadProfile.value.strategy.research_need ?? '',
    topic: threadProfile.value.screening.topic || project.value.topic,
    inclusion: threadProfile.value.screening.inclusion.length ? [...threadProfile.value.screening.inclusion] : [''],
    exclusion: threadProfile.value.screening.exclusion.length ? [...threadProfile.value.screening.exclusion] : [''],
    selectedDatabases: threadProfile.value.strategy.selected_databases.length
      ? [...threadProfile.value.strategy.selected_databases]
      : ['scopus', 'wos', 'pubmed', 'cnki']
  }
  editingThread.value = true
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

async function removeCurrentThread() {
  if (!project.value) return
  if (!window.confirm(`确认删除主题“${project.value.name}”？相关初筛和报告任务也会一起删除。`)) {
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
  [() => route.query.reportDatasetId, () => route.query.focusPanel],
  async ([datasetId, focusPanel]) => {
    if (focusPanel !== 'report' || typeof datasetId !== 'string' || datasetId !== fulltextReadyDataset.value?.id) {
      reportFocusNote.value = ''
      reportPanelHighlighted.value = false
      return
    }
    reportFocusNote.value = '全文已经准备好，下一步只需要确认报告主题和样式，然后生成报告。'
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

async function submitThreadReport() {
  if (!project.value || !fulltextReadyDataset.value || (fulltextReadyDataset.value.record_count ?? 0) <= 0) {
    message.warning('先到全文获取工作台把需要的文献标记为“已获取全文”')
    return
  }
  const preset = metaStore.providerPresets.find((item) => item.provider === 'deepseek') ?? metaStore.providerPresets[0]
  const task = await tasksStore.submitReport({
    title: reportTitle.value.trim() || `${project.value.name}-report`,
    project_id: project.value.id,
    screening_task_id: null,
    dataset_ids: [fulltextReadyDataset.value.id],
    project_topic: reportTopic.value.trim() || screeningDefaults.value?.topic || project.value.topic,
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
})
</script>

<template>
  <div v-if="project" class="thread-view">
    <section class="thread-brief panel-surface">
      <div class="thread-brief-head">
        <div>
          <div class="eyebrow">Thread Context</div>
          <h1>{{ project.name }}</h1>
          <p>{{ project.description || '这条线程会固定维护当前研究主题、筛选标准和各阶段进展。' }}</p>
        </div>
        <NSpace>
          <RouterLink :to="`/threads/${project.id}/plan/new`">
            <NButton tertiary>
              <template #icon><Sparkles :size="16" /></template>
              重新生成线程方案
            </NButton>
          </RouterLink>
          <NButton tertiary @click="openEditThread">
            <template #icon><Pencil :size="16" /></template>
            编辑主题与标准
          </NButton>
          <NButton tertiary type="error" @click="removeCurrentThread">
            <template #icon><Trash2 :size="16" /></template>
            删除线程
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
          <div class="brief-value">{{ screeningDefaults?.topic || project.topic }}</div>
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
          <NTag round type="warning">全文已获取 {{ fulltextCounts.ready }} 篇</NTag>
        </div>
        <NSpace>
          <RouterLink :to="`/threads/${project.id}/screening/new`">
            <NButton type="primary">
              <template #icon><FileSearch :size="16" /></template>
              开始新一轮初筛
            </NButton>
          </RouterLink>
          <RouterLink :to="`/threads/${project.id}/fulltext`">
            <NButton secondary>
              <template #icon><BookOpenText :size="16" /></template>
              进入统一复核
            </NButton>
          </RouterLink>
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

    <section class="metrics-grid">
      <OverviewMetric label="线程方案" :value="threadStats.strategies" />
      <OverviewMetric label="初筛轮次" :value="threadStats.rounds" />
      <OverviewMetric label="报告任务" :value="threadStats.reports" />
      <OverviewMetric label="累计纳入" :value="threadStats.cumulativeIncluded" />
      <OverviewMetric label="运行中" :value="threadStats.running" />
    </section>

    <div class="thread-layout">
      <section class="thread-main">
        <NCard title="阶段 1：线程方案" class="panel-surface">
          <template v-if="strategyContext?.plan">
            <div class="section-stack">
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
              <RouterLink v-if="latestStrategyTask" :to="`/tasks/${latestStrategyTask.id}`">
                <NButton tertiary>查看完整线程方案详情</NButton>
              </RouterLink>
            </div>
          </template>
          <NEmpty v-else description="还没有线程方案。先输入研究需求生成主题、标准和检索式。">
            <template #extra>
              <RouterLink :to="`/threads/${project.id}/plan/new`">
                <NButton type="primary">生成线程方案</NButton>
              </RouterLink>
            </template>
          </NEmpty>
        </NCard>

        <NCard title="阶段 2：初筛轮次" class="panel-surface">
          <div v-if="screeningRounds.length" class="message-stack">
            <ThreadMessageCard
              v-for="messageItem in threadMessages.filter((item) => item.kind === 'screening')"
              :key="messageItem.id"
              :message="messageItem"
            />
          </div>
          <NEmpty v-else description="当前线程还没有初筛轮次。生成线程方案后，就可以直接开始第一轮初筛。">
            <template #extra>
              <RouterLink :to="`/threads/${project.id}/screening/new`">
                <NButton type="primary">开始第一轮初筛</NButton>
              </RouterLink>
            </template>
          </NEmpty>
        </NCard>

        <NCard title="阶段 3：统一复核工作台" class="panel-surface">
          <div class="fulltext-summary-card">
            <div class="fulltext-summary-copy">
              这个工作台把“筛选复核”和“全文获取”收在同一页里。你可以先修正当前筛选结论，再只对仍然纳入的记录处理全文状态。
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
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext`, query: { status: 'excluded' } }">
                <NTag round type="error" :bordered="false" class="summary-tag">最终排除 {{ fulltextCounts.excluded }}</NTag>
              </RouterLink>
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext`, query: { status: 'unavailable' } }">
                <NTag round type="error" :bordered="false" class="summary-tag">无权限 {{ fulltextCounts.unavailable }}</NTag>
              </RouterLink>
              <RouterLink :to="{ path: `/threads/${project.id}/fulltext`, query: { status: 'deferred' } }">
                <NTag round type="warning" :bordered="false" class="summary-tag">暂缓 {{ fulltextCounts.deferred }}</NTag>
              </RouterLink>
            </div>
            <RouterLink :to="`/threads/${project.id}/fulltext`">
              <NButton type="primary">打开统一复核工作台</NButton>
            </RouterLink>
          </div>
        </NCard>

        <NCard ref="reportPanelRef" title="阶段 4：生成报告" class="panel-surface report-workspace-card" :class="{ highlighted: reportPanelHighlighted }">
          <NAlert v-if="reportFocusNote" type="warning" :show-icon="false" class="report-workspace-alert">
            {{ reportFocusNote }}
          </NAlert>
          <template v-if="fulltextReadyDataset && (fulltextReadyDataset.record_count ?? 0) > 0">
            <div class="report-workspace-copy">
              报告现在只接在全文获取之后。系统会默认使用当前线程里已标记为“已获取全文”的文献。
            </div>
            <div class="report-workspace-status">
              <NTag round type="success">已获取全文 {{ fulltextReadyDataset.record_count ?? 0 }} 篇</NTag>
            </div>
            <NForm label-placement="top" class="report-form">
              <NFormItem label="报告任务名称">
                <NInput v-model:value="reportTitle" placeholder="例如：某主题文献整理报告" />
              </NFormItem>
              <NFormItem label="报告主题">
                <NInput v-model:value="reportTopic" type="textarea" :autosize="{ minRows: 3, maxRows: 5 }" />
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
            <NButton type="primary" block @click="submitThreadReport">
              <template #icon><FileText :size="16" /></template>
              基于已获取全文生成报告
            </NButton>
          </template>
          <NAlert v-else type="info" :show-icon="false">
            先到全文获取工作台把需要的文献标记为“已获取全文”，这里才会开放报告生成。
          </NAlert>
        </NCard>
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
      title="编辑线程固定上下文"
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
          <NButton @click="editingThread = false">取消</NButton>
          <NButton type="primary" @click="saveThreadEdits">保存线程上下文</NButton>
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

.stage-grid,
.metrics-grid {
  display: grid;
  gap: 16px;
}

.stage-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.metrics-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
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
.report-workspace-status {
  margin-bottom: 14px;
}

.empty-thread {
  padding: 28px;
}

@media (max-width: 1200px) {
  .stage-grid,
  .metrics-grid {
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
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
