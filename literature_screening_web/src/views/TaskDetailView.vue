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
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import type { ScreeningRecordRow } from '@/types/api'

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
const reportDraft = computed(() => draftsStore.getReportDraft(taskId.value))
const selectedRecord = ref<ScreeningRecordRow | null>(null)
const reviewDecision = ref<'include' | 'exclude' | 'uncertain'>('include')
const reviewReason = ref('')
const bulkReviewDecision = ref<'include' | 'exclude' | 'uncertain'>('exclude')
const bulkReviewReason = ref('人工复核：批量剔除')
const bulkReviewText = ref('')
const referenceOverrideText = ref('')
const taskDatasetMap = computed(() => {
  const map = new Map()
  for (const dataset of projectsStore.currentProject?.datasets ?? []) {
    map.set(dataset.id, dataset)
  }
  return map
})
const originalIncludedDataset = computed(() => {
  if (task.value?.kind !== 'screening') return null
  const matches = task.value.output_dataset_ids
    .map((datasetId) => taskDatasetMap.value.get(datasetId) ?? null)
    .filter((dataset) => dataset?.kind === 'included')
  return matches.length ? matches[matches.length - 1] : null
})
const reviewedIncludedDataset = computed(() => {
  if (task.value?.kind !== 'screening') return null
  const matches = task.value.output_dataset_ids
    .map((datasetId) => taskDatasetMap.value.get(datasetId) ?? null)
    .filter((dataset) => dataset?.kind === 'included_reviewed')
  return matches.length ? matches[matches.length - 1] : null
})
const reportSourceOptions = computed(() => {
  const options: Array<{ label: string; value: 'original' | 'reviewed' }> = []
  if (originalIncludedDataset.value) {
    options.push({ label: `本轮原始纳入（${originalIncludedDataset.value.record_count ?? '-'} 篇）`, value: 'original' })
  }
  if (reviewedIncludedDataset.value) {
    options.push({ label: `人工复核后纳入（${reviewedIncludedDataset.value.record_count ?? '-'} 篇）`, value: 'reviewed' })
  }
  return options
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
    if (reviewedIncludedDataset.value && draft.sourceMode !== 'reviewed') {
      draftsStore.updateReportDraft(nextTask.id, { sourceMode: 'reviewed' })
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
  if (tasksStore.currentTask?.project_id) {
    await projectsStore.loadProject(tasksStore.currentTask.project_id)
  }
})

watch(taskId, async (nextTaskId, prevTaskId) => {
  if (!nextTaskId || nextTaskId === prevTaskId) return
  selectedRecord.value = null
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
  await tasksStore.loadTask(task.value.id, true)
  if (task.value.project_id) {
    await projectsStore.loadProject(task.value.project_id)
  }
  selectedRecord.value =
    tasksStore.currentTask?.records.find((row) => row.paper_id === selectedRecord.value?.paper_id) ?? null
  message.success('人工审核结果已保存')
}

async function submitBulkReviewOverride() {
  if (!task.value || !bulkReviewText.value.trim()) return
  await tasksStore.bulkReview(task.value.id, {
    entries_text: bulkReviewText.value,
    decision: bulkReviewDecision.value,
    reason: bulkReviewReason.value
  })
  await tasksStore.loadTask(task.value.id, true)
  if (task.value.project_id) {
    await projectsStore.loadProject(task.value.project_id)
  }
  selectedRecord.value = tasksStore.currentTask?.records[0] ?? null
  if (selectedRecord.value) {
    reviewDecision.value = selectedRecord.value.decision as 'include' | 'exclude' | 'uncertain'
    reviewReason.value = selectedRecord.value.reason || ''
  }
  bulkReviewText.value = ''
  message.success('批量人工修正已应用')
}

async function submitReport() {
  if (!task.value) return
  const preset = metaStore.providerPresets.find((item) => item.provider === 'deepseek') ?? metaStore.providerPresets[0]
  const useReviewedSource = reportDraft.value.sourceMode === 'reviewed' && Boolean(reviewedIncludedDataset.value?.id)
  const created = await tasksStore.submitReport({
    title: reportDraft.value.title,
    screening_task_id: useReviewedSource ? null : task.value.id,
    dataset_ids: useReviewedSource && reviewedIncludedDataset.value?.id ? [reviewedIncludedDataset.value.id] : [],
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
async function useStrategyForScreening() {
  if (!task.value || task.value.kind !== 'strategy') return
  await router.push(`/screening/new?projectId=${task.value.project_id ?? ''}&strategyTaskId=${task.value.id}`)
}
</script>

<template>
  <div v-if="task" class="task-detail-view">
    <section class="task-hero panel-surface">
      <div>
        <div class="eyebrow">{{ task.kind === 'strategy' ? 'Strategy Task' : task.kind === 'screening' ? 'Screening Task' : 'Report Task' }}</div>
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

    <template v-if="task.kind === 'strategy'">
      <section class="metrics-grid strategy-metrics">
        <OverviewMetric label="数据库" :value="task.strategy_plan?.search_blocks.length ?? 0" />
        <OverviewMetric label="纳入标准" :value="task.strategy_plan?.inclusion.length ?? 0" />
        <OverviewMetric label="排除标准" :value="task.strategy_plan?.exclusion.length ?? 0" />
      </section>

      <NCard title="检索与筛选方案" class="panel-surface">
        <div v-if="task.strategy_plan" class="strategy-stack">
          <div class="strategy-section">
            <div class="lineage-label">研究主题</div>
            <div class="lineage-value">{{ task.strategy_plan.topic }}</div>
          </div>
          <div class="strategy-section">
            <div class="lineage-label">建议用于初筛的研究主题</div>
            <div class="lineage-value">{{ task.strategy_plan.screening_topic }}</div>
          </div>
          <div class="strategy-section">
            <div class="lineage-label">需求概括</div>
            <div class="lineage-value">{{ task.strategy_plan.intent_summary }}</div>
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
          <div class="strategy-section">
            <div class="lineage-label">数据库检索式</div>
            <div class="search-blocks">
              <div v-for="block in task.strategy_plan.search_blocks" :key="block.database" class="search-block">
                <div class="search-block-head">{{ block.title }}</div>
                <pre v-if="block.query" class="search-code">{{ block.query }}</pre>
                <ul v-else class="bullet-list">
                  <li v-for="line in block.lines" :key="line">{{ line }}</li>
                </ul>
                <ul v-if="block.notes.length" class="bullet-list note-list">
                  <li v-for="note in block.notes" :key="note">{{ note }}</li>
                </ul>
              </div>
            </div>
          </div>
          <div v-if="task.strategy_plan.caution_notes.length" class="strategy-section">
            <div class="lineage-label">边界与注意事项</div>
            <ul class="bullet-list">
              <li v-for="note in task.strategy_plan.caution_notes" :key="note">{{ note }}</li>
            </ul>
          </div>
          <div class="report-action-row">
            <div class="report-copy">方案确认后，可以直接把主题与筛选标准带入初筛模块继续执行。</div>
            <NButton type="primary" @click="useStrategyForScreening">
              <template #icon>
                <FileText :size="16" />
              </template>
              带入初筛
            </NButton>
          </div>
        </div>
        <NAlert v-else type="info" :show-icon="false">策略任务完成后，这里会展示研究主题、筛选标准和高级检索式。</NAlert>
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
        <NFormItem label="报告来源" v-if="reportSourceOptions.length">
          <NSelect
            :value="reportDraft.sourceMode"
            @update:value="(value) => patchReportDraft({ sourceMode: value })"
            :options="reportSourceOptions"
          />
        </NFormItem>
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
            <NDivider />
            <div class="bulk-review-block">
              <div class="abstract-label">批量人工修正</div>
              <div class="report-copy">
                支持整段参考文献列表，或一行一个标题。系统会自动匹配当前筛选记录并批量应用。
              </div>
              <NForm label-placement="top">
                <NFormItem label="批量判定结果">
                  <NSelect
                    v-model:value="bulkReviewDecision"
                    :options="[
                      { label: '纳入', value: 'include' },
                      { label: '剔除', value: 'exclude' },
                      { label: '不确定', value: 'uncertain' }
                    ]"
                  />
                </NFormItem>
                <NFormItem label="批量审核理由">
                  <NInput v-model:value="bulkReviewReason" />
                </NFormItem>
                <NFormItem label="标题或参考文献列表">
                  <NInput
                    v-model:value="bulkReviewText"
                    type="textarea"
                    :autosize="{ minRows: 6, maxRows: 12 }"
                    placeholder="支持整段参考文献列表，或一行一个标题"
                  />
                </NFormItem>
              </NForm>
              <NButton type="primary" secondary @click="submitBulkReviewOverride" :disabled="!bulkReviewText.trim()">
                一键批量应用
              </NButton>
            </div>
          </template>
          <NAlert v-else type="info" :show-icon="false">从左侧表格选择一篇文献后，可在这里做人工修正。</NAlert>
        </NCard>
      </section>
    </template>

    <template v-else-if="task.kind === 'report'">
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

.strategy-metrics {
  grid-template-columns: repeat(3, minmax(0, 1fr));
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

.strategy-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.strategy-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.bullet-list {
  margin: 0;
  padding-left: 18px;
  color: #435046;
  line-height: 1.7;
}

.search-blocks {
  display: flex;
  flex-direction: column;
  gap: 14px;
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

.note-list {
  margin-top: 10px;
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
  .lineage-grid,
  .strategy-grid {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
