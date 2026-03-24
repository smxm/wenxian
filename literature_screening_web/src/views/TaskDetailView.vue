<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { FileText, RefreshCw, RotateCcw, Square } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NDivider,
  NForm,
  NFormItem,
  NGrid,
  NGridItem,
  NInput,
  NInputNumber,
  NProgress,
  NSelect,
  NSpace,
  NSpin,
  NText,
  useMessage
} from 'naive-ui'
import ArtifactList from '@/components/ArtifactList.vue'
import MarkdownArticle from '@/components/MarkdownArticle.vue'
import OverviewMetric from '@/components/OverviewMetric.vue'
import ScreeningRecordsTable from '@/components/ScreeningRecordsTable.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useDraftsStore } from '@/stores/drafts'
import { useMetaStore } from '@/stores/meta'
import { useTasksStore } from '@/stores/tasks'
import type { ScreeningRecordRow } from '@/types/api'

const route = useRoute()
const router = useRouter()
const tasksStore = useTasksStore()
const metaStore = useMetaStore()
const draftsStore = useDraftsStore()
const message = useMessage()

const taskId = computed(() => String(route.params.taskId))
const task = computed(() => tasksStore.currentTask)
const isRunning = computed(() => task.value?.status === 'running' || task.value?.status === 'pending')
const isScreeningTask = computed(() => task.value?.kind === 'screening')
const isRetriableTask = computed(() => task.value?.status === 'failed' || task.value?.status === 'cancelled')
const reportDraft = computed(() => draftsStore.getReportDraft(taskId.value))
const selectedRecord = ref<ScreeningRecordRow | null>(null)
const reviewDecision = ref<'include' | 'exclude' | 'uncertain'>('include')
const reviewReason = ref('')
const referenceOverrideText = ref('')

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

watch(
  () => task.value,
  (nextTask) => {
    if (!nextTask || nextTask.kind !== 'screening') return
    const draft = draftsStore.getReportDraft(nextTask.id)
    if (!draft.projectTopic && nextTask.project_topic) {
      draftsStore.updateReportDraft(nextTask.id, { projectTopic: nextTask.project_topic })
    }
    if (!draft.title || draft.title === `${nextTask.id}-report`) {
      draftsStore.updateReportDraft(nextTask.id, { title: `${nextTask.title}-report` })
    }
    if (!selectedRecord.value && nextTask.records.length) {
      selectedRecord.value = nextTask.records[0]
      reviewDecision.value = nextTask.records[0].decision as 'include' | 'exclude' | 'uncertain'
      reviewReason.value = nextTask.records[0].reason || ''
    }
  },
  { immediate: true }
)

onMounted(async () => {
  draftsStore.hydrate()
  await metaStore.ensureLoaded()
  await tasksStore.loadTask(taskId.value)
})

watch(taskId, async (nextTaskId, prevTaskId) => {
  if (!nextTaskId || nextTaskId === prevTaskId) return
  selectedRecord.value = null
  await tasksStore.loadTask(nextTaskId)
})

function handleSelectRecord(row: ScreeningRecordRow) {
  selectedRecord.value = row
  reviewDecision.value = row.decision as 'include' | 'exclude' | 'uncertain'
  reviewReason.value = row.reason || ''
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

async function submitReviewOverride() {
  if (!task.value || !selectedRecord.value) return
  await tasksStore.review(task.value.id, {
    paper_id: selectedRecord.value.paper_id,
    decision: reviewDecision.value,
    reason: reviewReason.value
  })
  selectedRecord.value =
    tasksStore.currentTask?.records.find((row) => row.paper_id === selectedRecord.value?.paper_id) ?? null
  message.success('人工审核结果已保存')
}

async function submitReport() {
  if (!task.value) return
  const preset = metaStore.providerPresets.find((item) => item.provider === 'deepseek') ?? metaStore.providerPresets[0]
  const created = await tasksStore.submitReport({
    title: reportDraft.value.title,
    screening_task_id: task.value.id,
    dataset_ids: [],
    project_topic: reportDraft.value.projectTopic,
    report_name: reportDraft.value.reportName,
    retry_times: reportDraft.value.retryTimes,
    timeout_seconds: reportDraft.value.timeoutSeconds,
    reference_style: reportDraft.value.referenceStyle,
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
  draftsStore.clearReportDraft(task.value.id)
  message.success('简洁报告任务已创建')
  await router.push(`/tasks/${created.id}`)
}

function patchReportDraft(patch: Record<string, unknown>) {
  draftsStore.updateReportDraft(taskId.value, patch)
}

async function submitReferenceOverride() {
  if (!task.value || !referenceOverrideText.value.trim()) return
  await tasksStore.reviewReferences(task.value.id, referenceOverrideText.value)
  message.success('参考列表已按报告顺序重排，并生成修正版报告')
}
</script>

<template>
  <div v-if="task" class="task-detail-view">
    <section class="task-hero panel-surface">
      <div>
        <div class="eyebrow">{{ task.kind === 'screening' ? 'Screening Task' : 'Report Task' }}</div>
        <h1>{{ task.title }}</h1>
        <div class="hero-meta">
          <StatusPill :status="task.status" />
          <NText depth="3">阶段：{{ task.phase_label || task.phase }}</NText>
          <NText depth="3">尝试次数：{{ task.attempt_count }}</NText>
          <NText depth="3">更新时间：{{ dayjs(task.updated_at).format('YYYY-MM-DD HH:mm:ss') }}</NText>
          <NText depth="3" v-if="task.project_id">项目：{{ task.project_id }}</NText>
          <NText depth="3" v-if="task.parent_task_id">父任务：{{ task.parent_task_id }}</NText>
        </div>
      </div>
      <NSpace>
        <NButton tertiary @click="refreshCurrentTask">
          <template #icon>
            <RefreshCw :size="16" />
          </template>
          刷新
        </NButton>
        <NButton v-if="isRetriableTask" tertiary @click="retryCurrentTask">
          <template #icon>
            <RotateCcw :size="16" />
          </template>
          继续执行
        </NButton>
        <NButton v-if="isRunning" tertiary @click="cancelCurrentTask">
          <template #icon>
            <Square :size="14" />
          </template>
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
          <div class="progress-meta" v-if="task.progress_total">
            {{ task.progress_current || 0 }}/{{ task.progress_total }}
          </div>
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

    <template v-if="task.kind === 'screening'">
      <section class="metrics-grid">
        <OverviewMetric label="原始条目" :value="screeningSummary.raw_entries_count ?? 0" />
        <OverviewMetric label="去重后" :value="screeningSummary.deduped_entries_count ?? 0" />
        <OverviewMetric label="纳入" :value="screeningSummary.included_count ?? 0" />
        <OverviewMetric label="剔除" :value="screeningSummary.excluded_count ?? 0" />
        <OverviewMetric label="不确定" :value="screeningSummary.uncertain_count ?? 0" />
        <OverviewMetric label="已处理" :value="screeningSummary.processed_count ?? 0" />
      </section>

      <NCard v-if="task.status === 'succeeded'" title="生成简洁报告" class="panel-surface">
        <NForm label-placement="top">
          <NGrid :cols="2" :x-gap="16" :y-gap="10" responsive="screen" item-responsive>
            <NGridItem span="2">
              <NFormItem label="报告任务名称">
                <NInput
                  :value="reportDraft.title"
                  @update:value="(value) => patchReportDraft({ title: value })"
                  placeholder="报告任务名称"
                />
              </NFormItem>
            </NGridItem>
            <NGridItem span="2">
              <NFormItem label="报告主题">
                <NInput
                  :value="reportDraft.projectTopic"
                  @update:value="(value) => patchReportDraft({ projectTopic: value })"
                  placeholder="报告主题"
                />
              </NFormItem>
            </NGridItem>
            <NGridItem span="2 m:1">
              <NFormItem label="输出目录名">
                <NInput
                  :value="reportDraft.reportName"
                  @update:value="(value) => patchReportDraft({ reportName: value })"
                  placeholder="simple_report"
                />
              </NFormItem>
            </NGridItem>
            <NGridItem span="2 m:1">
              <NFormItem label="参考样式">
                <NSelect
                  :value="reportDraft.referenceStyle"
                  @update:value="(value) => patchReportDraft({ referenceStyle: value })"
                  :options="metaStore.referenceStyles.map((item) => ({ label: item.label, value: item.value }))"
                />
              </NFormItem>
            </NGridItem>
            <NGridItem span="2 m:1">
              <NFormItem label="重试次数">
                <NInputNumber
                  :value="reportDraft.retryTimes"
                  @update:value="(value) => patchReportDraft({ retryTimes: value ?? 6 })"
                  :min="0"
                  :max="10"
                />
              </NFormItem>
            </NGridItem>
            <NGridItem span="2 m:1">
              <NFormItem label="超时（秒）">
                <NInputNumber
                  :value="reportDraft.timeoutSeconds"
                  @update:value="(value) => patchReportDraft({ timeoutSeconds: value ?? 240 })"
                  :min="60"
                  :max="600"
                />
              </NFormItem>
            </NGridItem>
          </NGrid>
        </NForm>

        <NDivider />
        <div class="report-action-row">
          <div class="report-copy">报告任务会继承当前初筛结果，并在任务中心独立运行。</div>
          <NButton type="primary" @click="submitReport">
            <template #icon>
              <FileText :size="16" />
            </template>
            创建简洁报告任务
          </NButton>
        </div>
      </NCard>

      <section class="review-grid">
        <NCard title="筛选记录" class="panel-surface">
          <ScreeningRecordsTable
            :rows="task.records"
            :selected-paper-id="selectedRecord?.paper_id ?? null"
            @select="handleSelectRecord"
          />
        </NCard>

        <NCard title="人工审核与修正" class="panel-surface">
          <template v-if="selectedRecord">
            <div class="review-meta">
              <div class="review-title">{{ selectedRecord.title }}</div>
              <div class="review-submeta">
                <span>{{ selectedRecord.year || '年份未知' }}</span>
                <span>{{ selectedRecord.journal || '期刊未知' }}</span>
              </div>
            </div>
            <div class="abstract-block">
              <div class="abstract-label">摘要信息</div>
              <div class="abstract-panel">
                {{ selectedRecord.abstract || '当前记录没有可用摘要。' }}
              </div>
            </div>
            <NForm label-placement="top">
              <NFormItem label="判定结果">
                <NSelect
                  v-model:value="reviewDecision"
                  :options="[
                    { label: '纳入', value: 'include' },
                    { label: '剔除', value: 'exclude' },
                    { label: '不确定', value: 'uncertain' }
                  ]"
                />
              </NFormItem>
              <NFormItem label="审核理由">
                <NInput v-model:value="reviewReason" type="textarea" :autosize="{ minRows: 4, maxRows: 8 }" />
              </NFormItem>
            </NForm>
            <NButton type="primary" @click="submitReviewOverride">保存人工审核结果</NButton>
          </template>
          <NAlert v-else type="info" :show-icon="false">从左侧表格选择一篇文献后，可在这里做人工修正。</NAlert>
        </NCard>
      </section>
    </template>

    <template v-if="task.kind === 'report'">
      <MarkdownArticle v-if="task.markdown_preview" :source="task.markdown_preview" />
      <NAlert v-else type="info" :show-icon="false">
        报告任务已创建。完成后这里会直接显示 Markdown 预览。
      </NAlert>

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

    <section class="bottom-grid">
      <NCard title="任务链与数据集" class="panel-surface">
        <div class="lineage-grid">
          <div>
            <div class="lineage-label">输入数据集</div>
            <div class="lineage-value">{{ task.input_dataset_ids.length ? task.input_dataset_ids.join('，') : '无' }}</div>
          </div>
          <div>
            <div class="lineage-label">输出数据集</div>
            <div class="lineage-value">{{ task.output_dataset_ids.length ? task.output_dataset_ids.join('，') : '无' }}</div>
          </div>
        </div>
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
    </section>
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

.review-grid,
.bottom-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 18px;
}

.progress-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.progress-label {
  font-weight: 700;
}

.progress-meta,
.progress-copy,
.report-copy {
  color: #5b665d;
}

.report-action-row {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
}

.reference-override-form {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.lineage-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.lineage-label {
  font-weight: 700;
}

.lineage-value {
  margin-top: 6px;
  color: #5b665d;
  word-break: break-word;
}

.review-meta {
  margin-bottom: 12px;
}

.review-title {
  font-weight: 700;
  line-height: 1.5;
}

.review-submeta {
  margin-top: 6px;
  display: flex;
  gap: 12px;
  color: #5b665d;
  font-size: 13px;
}

.abstract-block {
  margin-bottom: 14px;
}

.abstract-label {
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #526054;
}

.abstract-panel {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(241, 245, 240, 0.85);
  border: 1px solid rgba(86, 112, 92, 0.12);
  color: #435046;
  line-height: 1.7;
  white-space: pre-wrap;
  max-height: 220px;
  overflow: auto;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-item {
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.event-item:first-child {
  padding-top: 0;
  border-top: none;
}

.event-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #5b665d;
  font-size: 13px;
}

.event-message {
  margin-top: 6px;
}

.error-block {
  white-space: pre-wrap;
  margin: 0;
  font-family: Consolas, monospace;
}

@media (max-width: 1200px) {
  .metrics-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .review-grid,
  .bottom-grid,
  .task-hero,
  .report-action-row,
  .lineage-grid {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
