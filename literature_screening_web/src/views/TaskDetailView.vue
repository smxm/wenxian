<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { ArrowLeft, BookOpenText, FileText, RefreshCw, RotateCcw, Square } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NInput,
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
import type { DatasetRecord, ScreeningRecordRow } from '@/types/api'

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
const selectedRecord = ref<ScreeningRecordRow | null>(null)
const selectedPaperIds = ref<string[]>([])
const reviewDecision = ref<'include' | 'exclude' | 'uncertain'>('include')
const reviewReason = ref('')
const bulkReviewDecision = ref<'include' | 'exclude' | 'uncertain'>('exclude')
const bulkReviewReason = ref('人工复核：批量修正')
const bulkReviewText = ref('')
const referenceOverrideText = ref('')

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

const sourceSummary = computed(() => {
  if (!task.value?.input_dataset_ids.length) return task.value?.parent_task_id ? '延续上一轮未处理文献' : '新上传文献'
  return task.value.input_dataset_ids
    .map((datasetId) => datasetMap.value.get(datasetId)?.label ?? datasetId)
    .join(' + ')
})

const continueUnusedRoute = computed(() => {
  if (!task.value?.project_id || !unusedDataset.value) return null
  return `/threads/${task.value.project_id}/screening/new?sourceDatasetId=${unusedDataset.value.id}&parentTaskId=${task.value.id}`
})

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

async function cancelCurrentTask() {
  if (!task.value) return
  await tasksStore.cancel(task.value.id)
  message.success('已请求停止当前任务')
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
        <NButton tertiary @click="refreshCurrentTask">
          <template #icon><RefreshCw :size="16" /></template>
          刷新
        </NButton>
        <NButton v-if="isRetriableTask" tertiary @click="retryCurrentTask">
          <template #icon><RotateCcw :size="16" /></template>
          继续执行
        </NButton>
        <NButton v-if="isRunning" tertiary @click="cancelCurrentTask">
          <template #icon><Square :size="14" /></template>
          停止当前任务
        </NButton>
      </NSpace>
    </section>

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
      <template #description>报告任务正在整理单篇摘要、参考列表和最终 Markdown。</template>
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

      <NCard title="下一步：进入统一复核工作台" class="panel-surface">
        <div class="report-action-row">
          <div class="report-copy">常规复核现在建议直接放到“统一复核工作台”里做。那里是一条连续流程，左边看候选文献流，右边直接处理筛选判定和全文状态，不再在这里重复维护筛选记录表。</div>
          <NButton type="primary" @click="goToFulltextWorkspace" :disabled="!task.project_id">
            <template #icon><BookOpenText :size="16" /></template>
            去统一复核工作台
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
            <div class="summary-item">
              <span>模型</span>
              <strong>{{ task.model_provider || '未记录' }}</strong>
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
            <NTag v-if="includedDataset" round type="success">纳入集 {{ includedDataset.record_count ?? 0 }} 篇</NTag>
            <NTag v-if="unusedDataset" round>未使用 {{ unusedDataset.record_count ?? 0 }} 篇</NTag>
            <NTag v-if="excludedDataset" round type="error">剔除集 {{ excludedDataset.record_count ?? 0 }} 篇</NTag>
          </div>
        </NCard>

        <NCard title="线程主题与标准" class="panel-surface">
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
          <NAlert v-else type="info" :show-icon="false">当前线程还没有固定的主题与标准快照，先回线程主页补全或重新生成线程方案。</NAlert>
        </NCard>
      </section>

      <NCard title="本轮产出与后续动作" class="panel-surface">
        <div class="summary-item">
          <span>这页现在做什么</span>
          <strong>这里只保留本轮摘要、主题标准和产出边界。真正的筛选改判与全文处理统一在“统一复核工作台”里完成，避免同一批记录在两个页面重复出现。</strong>
        </div>
        <div class="tag-row" style="margin-top: 14px;">
          <NTag v-if="includedDataset" round type="success">可进入统一复核 {{ includedDataset.record_count ?? 0 }} 篇</NTag>
          <NTag v-if="unusedDataset" round>可继续筛选 {{ unusedDataset.record_count ?? 0 }} 篇</NTag>
          <NTag v-if="excludedDataset" round type="error">本轮已剔除 {{ excludedDataset.record_count ?? 0 }} 篇</NTag>
        </div>
        <div class="report-action-row" style="margin-top: 16px;">
          <div class="report-copy">如果要继续处理本轮纳入文献，直接去统一复核工作台；如果这轮还有未使用文献，也可以从这里直接开启下一轮。</div>
          <NSpace>
            <RouterLink v-if="continueUnusedRoute" :to="continueUnusedRoute">
              <NButton tertiary>继续筛选未使用文献</NButton>
            </RouterLink>
            <NButton type="primary" @click="goToFulltextWorkspace" :disabled="!task.project_id">打开统一复核工作台</NButton>
          </NSpace>
        </div>
      </NCard>
    </template>

    <template v-else-if="task.kind === 'report'">
      <MarkdownArticle v-if="task.markdown_preview" :source="task.markdown_preview" />
      <NAlert v-else type="info" :show-icon="false">报告任务已创建。完成后这里会直接显示 Markdown 预览。</NAlert>

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
