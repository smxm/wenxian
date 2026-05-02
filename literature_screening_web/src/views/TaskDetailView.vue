<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { ArrowLeft, BookOpenText, FileText, Pencil, RefreshCw, RotateCcw, Square, Trash2 } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NProgress,
  NSpace,
  NSpin,
  NTag,
  NText,
  useMessage
} from 'naive-ui'
import ArtifactList from '@/components/ArtifactList.vue'
import MarkdownArticle from '@/components/MarkdownArticle.vue'
import OverviewMetric from '@/components/OverviewMetric.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useMetaStore } from '@/stores/meta'
import { useDraftsStore } from '@/stores/drafts'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import type { DatasetRecord, ProviderName, ReferenceStyle, ScreeningRecordRow, TaskDetail as TaskDetailPayload } from '@/types/api'

const route = useRoute()
const router = useRouter()
const tasksStore = useTasksStore()
const metaStore = useMetaStore()
const draftsStore = useDraftsStore()
const projectsStore = useProjectsStore()
const message = useMessage()

const taskId = computed(() => String(route.params.taskId))
const task = computed(() => tasksStore.currentTask)
const isRunning = computed(() => task.value?.status === 'running' || task.value?.status === 'pending')
const isRetriableTask = computed(() => task.value?.status === 'failed' || task.value?.status === 'cancelled')
const canDeleteTask = computed(() => task.value?.kind === 'screening' && !isRunning.value)
const selectedRecord = ref<ScreeningRecordRow | null>(null)
const selectedPaperIds = ref<string[]>([])
const reviewDecision = ref<'include' | 'exclude' | 'uncertain'>('include')
const reviewReason = ref('')
const bulkReviewDecision = ref<'include' | 'exclude' | 'uncertain'>('exclude')
const bulkReviewReason = ref('人工复核：批量修正')
const bulkReviewText = ref('')
const referenceOverrideText = ref('')
const showRenameTaskModal = ref(false)
const renameTaskTitle = ref('')

const selectedRecords = computed(() => {
  const map = new Map((task.value?.records ?? []).map((row) => [row.paper_id, row]))
  return selectedPaperIds.value.map((paperId) => map.get(paperId)).filter((row): row is ScreeningRecordRow => Boolean(row))
})

const screeningSummary = computed<Record<string, number | string>>(() => {
  const source = task.value?.summary ?? {}
  return {
    raw_entries_count: Number(source.raw_entries_count ?? 0),
    deduped_entries_count: Number(source.deduped_entries_count ?? 0),
    included_count: Number(source.included_count ?? 0),
    excluded_count: Number(source.excluded_count ?? 0),
    uncertain_count: Number(source.uncertain_count ?? 0),
    processed_count: Number(source.processed_count ?? 0)
  }
})

const progressPercentage = computed(() => {
  const current = task.value?.progress_current
  const total = task.value?.progress_total
  if (!total || total <= 0 || current === null || current === undefined) return null
  return Math.max(0, Math.min(100, Math.round((current / total) * 100)))
})
const threadHomePath = computed(() => (task.value?.project_id ? `/threads/${task.value.project_id}` : null))
const threadEditPath = computed(() => (
  task.value?.project_id && task.value.kind !== 'screening'
    ? { path: `/threads/${task.value.project_id}`, query: { editThread: '1' } }
    : null
))
const currentProject = computed(() => projectsStore.currentProject)
const threadScreening = computed(() => currentProject.value?.thread_profile?.screening ?? null)

const datasetMap = computed(() => {
  const map = new Map<string, DatasetRecord>()
  for (const dataset of currentProject.value?.datasets ?? []) {
    map.set(dataset.id, dataset)
  }
  return map
})

function latestMatchingDataset(taskRecord: { output_dataset_ids: string[] }, kinds: string[]) {
  const matches = taskRecord.output_dataset_ids
    .map((datasetId) => datasetMap.value.get(datasetId) ?? null)
    .filter((dataset): dataset is DatasetRecord => Boolean(dataset && kinds.includes(dataset.kind)))
  return matches.length ? matches[matches.length - 1] : null
}

const includedDataset = computed(() => (task.value?.kind === 'screening' ? latestMatchingDataset(task.value, ['included_reviewed', 'included']) : null))
const unusedDataset = computed(() => (task.value?.kind === 'screening' ? latestMatchingDataset(task.value, ['unused']) : null))
const excludedDataset = computed(() => (task.value?.kind === 'screening' ? latestMatchingDataset(task.value, ['excluded_reviewed', 'excluded']) : null))
const canRenameScreeningTask = computed(() => task.value?.kind === 'screening')
const canReturnToEdit = computed(() => isRetriableTask.value && task.value?.kind === 'report')

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  return value as Record<string, unknown>
}

function asString(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []
}

const taskPayload = computed(() => asRecord(task.value?.request_payload))
const uploadedFileNames = computed(() => asStringArray(taskPayload.value?.uploaded_file_names))
const minIncludeConfidenceLabel = computed(() => {
  const value = asNumber(taskPayload.value?.min_include_confidence, 0.8) ?? 0.8
  return value > 0 ? `${Math.round(value * 100)}%` : '模型判定'
})
const taskScreeningCriteria = computed(() => {
  const payload = taskPayload.value
  if (!payload) return null
  const topic = asString(payload.topic).trim()
  const inclusion = asStringArray(payload.inclusion)
  const exclusion = asStringArray(payload.exclusion)
  if (!topic && !inclusion.length && !exclusion.length) return null
  return { topic, inclusion, exclusion }
})

const sourceSummary = computed(() => {
  const datasetSummary = (task.value?.input_dataset_ids ?? [])
    .map((datasetId) => datasetMap.value.get(datasetId)?.label ?? datasetId)
    .join(' + ')
  if (datasetSummary && uploadedFileNames.value.length) return `${datasetSummary} + 本轮上传文件`
  if (datasetSummary) return datasetSummary
  if (uploadedFileNames.value.length) return task.value?.parent_task_id ? '延续上一轮并补充上传文件' : '新上传文献'
  return task.value?.parent_task_id ? '延续上一轮未处理文献' : '新上传文献'
})

function asBoolean(value: unknown, fallback = false): boolean {
  return typeof value === 'boolean' ? value : fallback
}

function asNumber(value: unknown, fallback: number | null): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    if (Number.isFinite(parsed)) return parsed
  }
  return fallback
}

function asProvider(value: unknown, fallback: ProviderName = 'deepseek'): ProviderName {
  return value === 'kimi' || value === 'deepseek' ? value : fallback
}

function asReferenceStyle(value: unknown, fallback: ReferenceStyle = 'gbt7714'): ReferenceStyle {
  return value === 'apa7' || value === 'gbt7714' ? value : fallback
}

function ensureDynamicList(items: string[]): string[] {
  return items.length ? items : ['']
}

function restoreScreeningDraftFromTask(taskDetail: TaskDetailPayload): boolean {
  const payload = asRecord(taskDetail.request_payload)
  if (!payload) return false

  const provider = asProvider(payload.provider)
  draftsStore.setScreeningFiles([])
  draftsStore.updateScreeningDraft({
    projectId: taskDetail.project_id || asString(payload.project_id) || null,
    newProjectName: '',
    newProjectDescription: '',
    sourceDatasetIds: asStringArray(payload.source_dataset_ids),
    parentTaskId: asString(payload.parent_task_id) || taskDetail.parent_task_id || null,
    selectedTemplateId: null,
    title: asString(payload.title) || taskDetail.title,
    topic: asString(payload.topic) || taskDetail.project_topic || '',
    criteriaMarkdown: asString(payload.criteria_markdown),
    inclusion: ensureDynamicList(asStringArray(payload.inclusion)),
    exclusion: ensureDynamicList(asStringArray(payload.exclusion)),
    provider,
    model: {
      provider,
      model_name: asString(payload.model_name, provider === 'kimi' ? 'moonshot-v1-auto' : 'deepseek-chat'),
      api_base_url: asString(payload.api_base_url, provider === 'kimi' ? 'https://api.moonshot.cn/v1' : 'https://api.deepseek.com/v1'),
      api_key_env: asString(payload.api_key_env, provider === 'kimi' ? 'KIMI_API_KEY' : 'DEEPSEEK_API_KEY'),
      api_key: draftsStore.getProviderApiKey(provider),
      temperature: asNumber(payload.temperature, 0) ?? 0,
      max_tokens: Math.max(asNumber(payload.max_tokens, 4096) ?? 4096, 4096),
      min_request_interval_seconds: asNumber(payload.min_request_interval_seconds, 2) ?? 2,
    },
    batchSize: asNumber(payload.batch_size, 10) ?? 10,
    targetIncludeCount: asNumber(payload.target_include_count, null),
    stopWhenReached: asBoolean(payload.stop_when_target_reached, false),
    minIncludeConfidence: asNumber(payload.min_include_confidence, 0.8) ?? 0.8,
    allowUncertain: asBoolean(payload.allow_uncertain, true),
    retryTimes: asNumber(payload.retry_times, 6) ?? 6,
    requestTimeout: asNumber(payload.request_timeout_seconds, 240) ?? 240,
    encoding: asString(payload.encoding, 'auto'),
    fileNames: asStringArray(payload.uploaded_file_names),
  })
  return true
}

function restoreReportDraftFromTask(taskDetail: TaskDetailPayload): boolean {
  const payload = asRecord(taskDetail.request_payload)
  if (!payload || !taskDetail.project_id) return false

  const modelPayload = asRecord(payload.model)
  const provider = asProvider(modelPayload?.provider)
  draftsStore.updateReportDraft(taskDetail.project_id, {
    projectId: taskDetail.project_id,
    screeningTaskId: asString(payload.screening_task_id) || null,
    datasetIds: asStringArray(payload.dataset_ids),
    title: asString(payload.title) || taskDetail.title,
    projectTopic: asString(payload.project_topic) || taskDetail.project_topic || '',
    reportName: asString(payload.report_name, 'simple_report'),
    referenceStyle: asReferenceStyle(payload.reference_style, 'gbt7714'),
    retryTimes: asNumber(payload.retry_times, 6) ?? 6,
    timeoutSeconds: asNumber(payload.timeout_seconds, 240) ?? 240,
    provider,
    modelName: asString(modelPayload?.model_name, provider === 'kimi' ? 'moonshot-v1-auto' : 'deepseek-reasoner'),
    apiBaseUrl: asString(modelPayload?.api_base_url, provider === 'kimi' ? 'https://api.moonshot.cn/v1' : 'https://api.deepseek.com/v1'),
    apiKeyEnv: asString(modelPayload?.api_key_env, provider === 'kimi' ? 'KIMI_API_KEY' : 'DEEPSEEK_API_KEY'),
  })
  return true
}

watch(
  () => task.value,
  (nextTask) => {
    if (!nextTask || nextTask.kind !== 'screening') return
    if (!selectedRecord.value && nextTask.records.length) {
      selectedRecord.value = nextTask.records[0]
      reviewDecision.value = nextTask.records[0].decision as 'include' | 'exclude' | 'uncertain'
      reviewReason.value = nextTask.records[0].reason || ''
    }
    if (!selectedPaperIds.value.length && nextTask.records.length) {
      selectedPaperIds.value = [nextTask.records[0].paper_id]
    }
  },
  { immediate: true }
)

watch(selectedPaperIds, (nextPaperIds) => {
  if (!nextPaperIds.length) return
  if (nextPaperIds.length === 1) {
    const row = task.value?.records.find((item) => item.paper_id === nextPaperIds[0]) ?? null
    if (row) {
      selectedRecord.value = row
      reviewDecision.value = row.decision as 'include' | 'exclude' | 'uncertain'
      reviewReason.value = row.reason || ''
    }
  }
})

onMounted(async () => {
  draftsStore.hydrate()
  await metaStore.ensureLoaded()
  await tasksStore.loadTask(taskId.value)
  if (tasksStore.currentTask?.project_id) {
    await projectsStore.loadProject(tasksStore.currentTask.project_id)
  }
})

watch(taskId, async (nextTaskId, prevTaskId) => {
  if (!nextTaskId || nextTaskId === prevTaskId) return
  selectedRecord.value = null
  selectedPaperIds.value = []
  await tasksStore.loadTask(nextTaskId)
  if (tasksStore.currentTask?.project_id) {
    await projectsStore.loadProject(tasksStore.currentTask.project_id)
  }
})

function handleSelectRecord(row: ScreeningRecordRow) {
  selectedRecord.value = row
  reviewDecision.value = row.decision as 'include' | 'exclude' | 'uncertain'
  reviewReason.value = row.reason || ''
}

function handleSelectionChange(paperIds: string[]) {
  selectedPaperIds.value = paperIds
}

async function refreshCurrentTask() {
  await tasksStore.loadTask(taskId.value)
}

async function retryCurrentTask() {
  if (!task.value) return
  await tasksStore.retry(task.value.id, 'resume')
  message.success('任务已重新启动')
}

function openRenameTaskModal() {
  if (!task.value || task.value.kind !== 'screening') return
  renameTaskTitle.value = task.value.title
  showRenameTaskModal.value = true
}

async function saveTaskRename() {
  if (!task.value || task.value.kind !== 'screening') return
  const nextTitle = renameTaskTitle.value.trim()
  if (!nextTitle) {
    message.warning('任务名称不能为空')
    return
  }
  await tasksStore.rename(task.value.id, nextTitle)
  if (task.value.project_id) {
    await projectsStore.loadProject(task.value.project_id)
  }
  showRenameTaskModal.value = false
  message.success('初筛任务名称已更新')
}

async function cloneScreeningTaskAsNewRound() {
  if (!task.value || task.value.kind !== 'screening') return
  if (!restoreScreeningDraftFromTask(task.value)) {
    message.error('当前任务缺少可恢复的编辑参数')
    return
  }
  const targetPath = task.value.project_id ? `/threads/${task.value.project_id}/screening/new` : '/screening/new'
  await router.push(targetPath)
  message.success('已复制本轮初筛参数，可以作为新一轮重新提交')
}

async function returnTaskToEdit() {
  if (!task.value) return

  if (task.value.kind === 'report') {
    if (!task.value.project_id || !restoreReportDraftFromTask(task.value)) {
      message.error('当前报告生成任务缺少可恢复的编辑参数')
      return
    }
    await router.push({
      path: `/threads/${task.value.project_id}`,
      query: {
        focusPanel: 'report',
        reportDatasetId: task.value.input_dataset_ids[0] ?? undefined,
      },
    })
    message.success('已返回报告编辑区，可以修改参数后重新提交')
  }
}

async function cancelCurrentTask() {
  if (!task.value) return
  await tasksStore.cancel(task.value.id)
  message.success('已请求停止当前任务')
}

function requestErrorMessage(error: unknown, fallback: string) {
  if (!error || typeof error !== 'object') return fallback
  const response = (error as { response?: { data?: { detail?: unknown } } }).response
  return typeof response?.data?.detail === 'string' ? response.data.detail : fallback
}

async function deleteCurrentTask() {
  if (!task.value || !canDeleteTask.value) return
  const confirmed = window.confirm('删除这轮初筛后，它产生的纳入/剔除/未使用结果会一并移除，并从复核与全文工作台回收。这个操作不能撤销。确定继续吗？')
  if (!confirmed) return

  const projectId = task.value.project_id
  const targetTaskId = task.value.id
  try {
    await tasksStore.delete(targetTaskId)
    if (projectId) {
      await projectsStore.loadProject(projectId)
      await router.push(`/threads/${projectId}`)
    } else {
      await router.push('/tasks')
    }
    message.success('初筛轮次已删除')
  } catch (error) {
    message.error(requestErrorMessage(error, '删除初筛轮次失败'))
  }
}

async function reloadAfterReview() {
  if (!task.value) return
  await tasksStore.loadTask(task.value.id, true)
  if (task.value.project_id) {
    await projectsStore.loadProject(task.value.project_id)
  }
}

async function submitReviewOverride() {
  if (!task.value || !selectedRecord.value) return
  await tasksStore.review(task.value.id, {
    paper_id: selectedRecord.value.paper_id,
    decision: reviewDecision.value,
    reason: reviewReason.value
  })
  await reloadAfterReview()
  message.success('人工审核结果已保存')
}

async function submitSelectionReviewOverride() {
  if (!task.value || !selectedPaperIds.value.length) return
  await tasksStore.bulkReviewSelection(task.value.id, {
    paper_ids: selectedPaperIds.value,
    decision: bulkReviewDecision.value,
    reason: bulkReviewReason.value
  })
  await reloadAfterReview()
  message.success(`已批量更新 ${selectedPaperIds.value.length} 篇文献`)
}

async function submitBulkReviewOverride() {
  if (!task.value || !bulkReviewText.value.trim()) return
  await tasksStore.bulkReview(task.value.id, {
    entries_text: bulkReviewText.value,
    decision: bulkReviewDecision.value,
    reason: bulkReviewReason.value
  })
  await reloadAfterReview()
  bulkReviewText.value = ''
  message.success('按标题批量修正已应用')
}

async function submitReferenceOverride() {
  if (!task.value || !referenceOverrideText.value.trim()) return
  await tasksStore.reviewReferences(task.value.id, referenceOverrideText.value)
  message.success('参考列表已按报告顺序重排，并生成修正版报告')
}

async function useStrategyForScreening() {
  if (!task.value || task.value.kind !== 'strategy') return
  if (!task.value.project_id) return
  await router.push(`/threads/${task.value.project_id}/screening/new?strategyTaskId=${task.value.id}`)
}

async function goToFulltextWorkspace() {
  if (!task.value?.project_id) return
  await router.push(`/threads/${task.value.project_id}/fulltext?screeningTaskId=${task.value.id}`)
}
</script>

<template>
  <div v-if="task" class="task-detail-view">
    <section class="task-hero panel-surface">
      <div>
        <div class="eyebrow">{{ task.kind === 'strategy' ? 'Thread Plan' : task.kind === 'screening' ? 'Screening Round' : 'Report Task' }}</div>
        <h1>{{ task.title }}</h1>
        <div class="hero-meta">
          <StatusPill :status="task.status" />
          <NText depth="3">阶段：{{ task.phase_label || task.phase }}</NText>
          <NText v-if="currentProject?.name" depth="3">线程：{{ currentProject.name }}</NText>
          <NText depth="3">尝试次数：{{ task.attempt_count }}</NText>
          <NText depth="3">更新时间：{{ dayjs(task.updated_at).format('YYYY-MM-DD HH:mm:ss') }}</NText>
        </div>
      </div>
      <NSpace>
        <RouterLink v-if="threadHomePath" :to="threadHomePath">
          <NButton tertiary>
            <template #icon><ArrowLeft :size="16" /></template>
            返回线程主页
          </NButton>
        </RouterLink>
        <RouterLink v-if="threadEditPath" :to="threadEditPath">
          <NButton tertiary type="warning">
            <template #icon><Pencil :size="16" /></template>
            编辑线程信息
          </NButton>
        </RouterLink>
        <NButton v-if="canRenameScreeningTask" tertiary type="warning" @click="openRenameTaskModal">
          <template #icon><Pencil :size="16" /></template>
          重命名初筛
        </NButton>
        <NButton v-if="canRenameScreeningTask && !isRunning" tertiary @click="cloneScreeningTaskAsNewRound">
          <template #icon><FileText :size="16" /></template>
          复制为新一轮
        </NButton>
        <NButton tertiary @click="refreshCurrentTask">
          <template #icon><RefreshCw :size="16" /></template>
          刷新
        </NButton>
        <NButton v-if="isRetriableTask" tertiary @click="retryCurrentTask">
          <template #icon><RotateCcw :size="16" /></template>
          继续执行
        </NButton>
        <NButton v-if="canReturnToEdit" tertiary type="warning" @click="returnTaskToEdit">
          <template #icon><FileText :size="16" /></template>
          返回编辑
        </NButton>
        <NButton v-if="isRunning" tertiary @click="cancelCurrentTask">
          <template #icon><Square :size="14" /></template>
          停止当前任务
        </NButton>
        <NButton v-if="canDeleteTask" tertiary type="error" @click="deleteCurrentTask">
          <template #icon><Trash2 :size="14" /></template>
          删除本轮初筛
        </NButton>
      </NSpace>
    </section>

    <NModal
      v-model:show="showRenameTaskModal"
      preset="card"
      title="重命名初筛任务"
      style="width: 520px"
      :bordered="false"
    >
      <NForm label-placement="top">
        <NFormItem label="任务名称">
          <NInput
            v-model:value="renameTaskTitle"
            placeholder="例如：English batch 1"
            @keyup.enter="saveTaskRename"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showRenameTaskModal = false">取消</NButton>
          <NButton type="primary" :loading="tasksStore.submitting" @click="saveTaskRename">保存</NButton>
        </NSpace>
      </template>
    </NModal>

    <NAlert v-if="task.error" type="error" :show-icon="false">
      <pre class="error-block">{{ task.error }}</pre>
    </NAlert>

    <NCard v-if="isRunning" title="任务进度" class="panel-surface">
      <div class="progress-stack">
        <div class="progress-head">
          <div class="progress-label">{{ task.phase_label || task.phase }}</div>
          <div class="progress-meta" v-if="task.progress_total">{{ task.progress_current || 0 }}/{{ task.progress_total }}</div>
        </div>
        <NProgress
          type="line"
          :percentage="progressPercentage ?? 10"
          :indicator-placement="'inside'"
          :processing="true"
          :show-indicator="progressPercentage !== null"
        />
        <div class="progress-copy">{{ task.progress_message || '任务正在后台执行，页面会自动刷新最新状态。' }}</div>
      </div>
    </NCard>

    <NSpin v-if="isRunning && task.kind === 'report'" size="large">
      <template #description>报告生成任务正在整理单篇摘要、参考列表和最终 Markdown。</template>
    </NSpin>

    <template v-if="task.kind === 'strategy'">
      <section class="metrics-grid strategy-metrics">
        <OverviewMetric label="数据库" :value="task.strategy_plan?.search_blocks.length ?? 0" />
        <OverviewMetric label="纳入标准" :value="task.strategy_plan?.inclusion.length ?? 0" />
        <OverviewMetric label="排除标准" :value="task.strategy_plan?.exclusion.length ?? 0" />
      </section>

      <NCard title="线程方案" class="panel-surface">
        <div v-if="task.strategy_plan" class="strategy-stack">
          <div class="strategy-section">
            <div class="lineage-label">研究主题</div>
            <div class="lineage-value">{{ task.strategy_plan.topic }}</div>
          </div>
          <div class="strategy-section">
            <div class="lineage-label">建议用于初筛的线程主题</div>
            <div class="lineage-value">{{ task.strategy_plan.screening_topic }}</div>
          </div>
          <div class="strategy-grid">
            <div>
              <div class="lineage-label">纳入标准</div>
              <ul class="bullet-list">
                <li v-for="item in task.strategy_plan.inclusion" :key="item">{{ item }}</li>
              </ul>
            </div>
            <div>
              <div class="lineage-label">排除标准</div>
              <ul class="bullet-list">
                <li v-for="item in task.strategy_plan.exclusion" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
          <div class="report-action-row">
            <div class="report-copy">如果要把当前方案直接作为新的筛选轮次起点，可以一键带入初筛页。</div>
            <NButton type="primary" @click="useStrategyForScreening">
              <template #icon><FileText :size="16" /></template>
              带入初筛
            </NButton>
          </div>
        </div>
        <NAlert v-else type="info" :show-icon="false">线程方案完成后，这里会展示主题、筛选标准和检索式。</NAlert>
      </NCard>

      <MarkdownArticle v-if="task.markdown_preview" :source="task.markdown_preview" />
    </template>

    <template v-else-if="task.kind === 'screening'">
      <section class="metrics-grid">
        <OverviewMetric label="原始条目" :value="screeningSummary.raw_entries_count ?? 0" />
        <OverviewMetric label="去重后" :value="screeningSummary.deduped_entries_count ?? 0" />
        <OverviewMetric label="纳入" :value="screeningSummary.included_count ?? 0" />
        <OverviewMetric label="剔除" :value="screeningSummary.excluded_count ?? 0" />
        <OverviewMetric label="不确定" :value="screeningSummary.uncertain_count ?? 0" />
        <OverviewMetric label="已处理" :value="screeningSummary.processed_count ?? 0" />
      </section>

      <NCard title="下一步：进入复核与全文工作台" class="panel-surface">
        <div class="report-action-row">
          <div class="report-copy">后续处理直接在复核与全文工作台完成；生成报告时再选择需要的已获取全文批次。</div>
          <NButton type="primary" @click="goToFulltextWorkspace" :disabled="!task.project_id">
            <template #icon><BookOpenText :size="16" /></template>
            去复核与全文工作台
          </NButton>
        </div>
      </NCard>

      <section class="screening-overview-grid">
        <NCard title="本轮筛选摘要" class="panel-surface">
          <div class="screening-summary-stack">
            <div class="summary-item">
              <span>来源</span>
              <strong>{{ sourceSummary }}</strong>
            </div>
            <div v-if="uploadedFileNames.length" class="summary-item full">
              <span>上传文件</span>
              <div class="summary-tag-row">
                <NTag v-for="fileName in uploadedFileNames" :key="fileName" round>{{ fileName }}</NTag>
              </div>
            </div>
            <div class="summary-item">
              <span>模型</span>
              <strong>{{ task.model_provider || '未记录' }}</strong>
            </div>
            <div class="summary-item">
              <span>最低纳入相关度</span>
              <strong>{{ minIncludeConfidenceLabel }}</strong>
            </div>
            <div v-if="asNumber(taskPayload?.target_include_count, null)" class="summary-item">
              <span>目标纳入</span>
              <strong>
                {{ asNumber(taskPayload?.target_include_count, null) }} 篇
                {{ asBoolean(taskPayload?.stop_when_target_reached, false) ? '，达到后停止' : '，达到后继续筛选' }}
              </strong>
            </div>
            <div class="summary-item">
              <span>创建时间</span>
              <strong>{{ dayjs(task.created_at).format('YYYY-MM-DD HH:mm:ss') }}</strong>
            </div>
            <div class="summary-item">
              <span>最近更新</span>
              <strong>{{ dayjs(task.updated_at).format('YYYY-MM-DD HH:mm:ss') }}</strong>
            </div>
            <div v-if="task.progress_message" class="summary-item full">
              <span>运行备注</span>
              <strong>{{ task.progress_message }}</strong>
            </div>
          </div>
          <div class="tag-row">
            <NTag round>纳入 {{ screeningSummary.included_count ?? 0 }}</NTag>
            <NTag round>剔除 {{ screeningSummary.excluded_count ?? 0 }}</NTag>
            <NTag round>不确定 {{ screeningSummary.uncertain_count ?? 0 }}</NTag>
            <NTag
              v-if="asNumber(taskPayload?.target_include_count, null)"
              round
              :type="asBoolean(taskPayload?.stop_when_target_reached, false) ? 'success' : 'warning'"
            >
              {{ asBoolean(taskPayload?.stop_when_target_reached, false) ? '提前停止已启用' : '提前停止未启用' }}
            </NTag>
            <NTag v-if="includedDataset" round type="success">纳入集 {{ includedDataset.record_count ?? 0 }} 篇</NTag>
            <NTag v-if="unusedDataset" round>未使用 {{ unusedDataset.record_count ?? 0 }} 篇</NTag>
            <NTag v-if="excludedDataset" round type="error">剔除集 {{ excludedDataset.record_count ?? 0 }} 篇</NTag>
          </div>
        </NCard>

        <NCard title="本轮实际使用的主题与标准" class="panel-surface">
          <template v-if="taskScreeningCriteria">
            <div class="screening-summary-stack">
              <div>
                <div class="lineage-label">本轮主题</div>
                <div class="lineage-value">{{ taskScreeningCriteria.topic || '未记录' }}</div>
              </div>
              <div class="strategy-grid">
                <div>
                  <div class="lineage-label">纳入标准</div>
                  <ul class="bullet-list">
                    <li v-for="item in taskScreeningCriteria.inclusion" :key="item">{{ item }}</li>
                  </ul>
                </div>
                <div>
                  <div class="lineage-label">排除标准</div>
                  <ul class="bullet-list">
                    <li v-for="item in taskScreeningCriteria.exclusion" :key="item">{{ item }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </template>
          <NAlert v-else type="info" :show-icon="false">当前任务没有记录独立的筛选标准快照。</NAlert>
        </NCard>

        <NCard title="当前线程默认主题与标准" class="panel-surface">
          <template v-if="threadScreening">
            <div class="screening-summary-stack">
              <div>
                <div class="lineage-label">当前主题</div>
                <div class="lineage-value">{{ threadScreening.topic }}</div>
              </div>
              <div class="strategy-grid">
                <div>
                  <div class="lineage-label">纳入标准</div>
                  <ul class="bullet-list">
                    <li v-for="item in threadScreening.inclusion" :key="item">{{ item }}</li>
                  </ul>
                </div>
                <div>
                  <div class="lineage-label">排除标准</div>
                  <ul class="bullet-list">
                    <li v-for="item in threadScreening.exclusion" :key="item">{{ item }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </template>
          <NAlert v-else type="info" :show-icon="false">当前线程还没有主题与标准。</NAlert>
        </NCard>
      </section>
    </template>

    <template v-else-if="task.kind === 'report'">
      <MarkdownArticle v-if="task.markdown_preview" :source="task.markdown_preview" />
      <NAlert v-else type="info" :show-icon="false">报告生成任务已创建。完成后这里会直接显示 Markdown 预览。</NAlert>

      <NCard v-if="task.status === 'succeeded'" title="参考列表人工修正" class="panel-surface">
        <div class="report-copy">
          粘贴你从 Zotero 或其他来源修正后的参考列表。系统会按当前报告中的文献顺序自动重排，并替换报告尾部参考列表。
        </div>
        <div class="reference-override-form">
          <NInput
            v-model:value="referenceOverrideText"
            type="textarea"
            :autosize="{ minRows: 8, maxRows: 16 }"
            placeholder="把修正后的参考列表整段粘贴到这里"
          />
          <NButton type="primary" @click="submitReferenceOverride" :disabled="!referenceOverrideText.trim()">
            应用参考列表修正
          </NButton>
        </div>
      </NCard>
    </template>

    <NCard title="产物文件" class="panel-surface">
      <ArtifactList :task-id="task.id" :artifacts="task.artifacts" />
    </NCard>

    <NCard title="审计事件" class="panel-surface">
      <div v-if="task.events.length" class="event-list">
        <div v-for="event in task.events" :key="event.id" class="event-item">
          <div class="event-head">
            <strong>{{ event.kind }}</strong>
            <span>{{ dayjs(event.created_at).format('YYYY-MM-DD HH:mm:ss') }}</span>
          </div>
          <div class="event-message">{{ event.message }}</div>
        </div>
      </div>
      <NAlert v-else type="info" :show-icon="false">当前任务还没有审计事件。</NAlert>
    </NCard>
  </div>
</template>

<style scoped>
.task-detail-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.task-hero {
  padding: 22px 24px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 12px;
  color: #6a776c;
}

h1 {
  margin: 8px 0;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 16px;
}

.strategy-metrics {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.screening-overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.review-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 18px;
}

.progress-stack,
.strategy-stack,
.reference-override-form,
.screening-summary-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-head,
.report-action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.summary-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.progress-label,
.review-title {
  font-weight: 700;
}

.progress-meta,
.progress-copy,
.report-copy {
  color: #5b665d;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: #5b665d;
}

.summary-item.full {
  flex-direction: column;
}

.summary-item strong {
  color: #223025;
  text-align: right;
}

.summary-item.full strong {
  text-align: left;
  line-height: 1.7;
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.lineage-label,
.abstract-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #708074;
  margin-bottom: 8px;
}

.lineage-value {
  white-space: pre-wrap;
  line-height: 1.65;
}

.bullet-list {
  margin: 0;
  padding-left: 18px;
  color: #435046;
  line-height: 1.7;
}

.review-meta,
.bulk-review-block,
.abstract-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.review-submeta {
  display: flex;
  gap: 10px;
  color: #6a776c;
}

.abstract-panel {
  border-radius: 14px;
  padding: 14px;
  background: rgba(247, 249, 246, 0.94);
  border: 1px solid rgba(71, 95, 76, 0.12);
  line-height: 1.65;
  white-space: pre-wrap;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-item {
  padding: 14px;
  border-radius: 14px;
  background: rgba(247, 249, 246, 0.94);
}

.event-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.event-message {
  margin-top: 6px;
}

.error-block {
  white-space: pre-wrap;
}

@media (max-width: 1100px) {
  .metrics-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .screening-overview-grid,
  .review-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .task-hero,
  .report-action-row {
    flex-direction: column;
    align-items: stretch;
  }

  .metrics-grid,
  .strategy-grid {
    grid-template-columns: 1fr;
  }

  .summary-item {
    flex-direction: column;
  }

  .summary-item strong {
    text-align: left;
  }
}
</style>
