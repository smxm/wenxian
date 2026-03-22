<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { FileText, RefreshCw } from 'lucide-vue-next'
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
const reportDraft = computed(() => draftsStore.getReportDraft(taskId.value))

const screeningSummary = computed<Record<string, number | string>>(() => {
  const source = task.value?.summary ?? {}
  return {
    raw_entries_count: Number(source.raw_entries_count ?? 0),
    deduped_entries_count: Number(source.deduped_entries_count ?? 0),
    included_count: Number(source.included_count ?? 0),
    uncertain_count: Number(source.uncertain_count ?? 0)
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
  await tasksStore.loadTask(nextTaskId)
})

async function refreshCurrentTask() {
  await tasksStore.loadTask(taskId.value)
}

async function submitReport() {
  if (!task.value) return
  const preset = metaStore.providerPresets.find((item) => item.provider === 'deepseek') ?? metaStore.providerPresets[0]
  const created = await tasksStore.submitReport({
    title: reportDraft.value.title,
    screening_task_id: task.value.id,
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
      temperature: 0,
      max_tokens: 1536,
      min_request_interval_seconds: 2
    }
  })
  draftsStore.clearReportDraft(task.value.id)
  message.success('简洁报告任务已创建。')
  await router.push(`/tasks/${created.id}`)
}

function patchReportDraft(patch: Record<string, unknown>) {
  draftsStore.updateReportDraft(taskId.value, patch)
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
          <NText depth="3">更新时间：{{ dayjs(task.updated_at).format('YYYY-MM-DD HH:mm:ss') }}</NText>
        </div>
      </div>
      <NSpace>
        <NButton tertiary @click="refreshCurrentTask">
          <template #icon>
            <RefreshCw :size="16" />
          </template>
          刷新
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
      <template #description>报告任务正在整理单篇文献、参考列表和最终 Markdown。</template>
    </NSpin>

    <template v-if="task.kind === 'screening'">
      <section class="metrics-grid">
        <OverviewMetric label="原始条目" :value="screeningSummary.raw_entries_count ?? 0" />
        <OverviewMetric label="去重后" :value="screeningSummary.deduped_entries_count ?? 0" />
        <OverviewMetric label="纳入" :value="screeningSummary.included_count ?? 0" />
        <OverviewMetric label="不确定" :value="screeningSummary.uncertain_count ?? 0" />
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
          <div class="report-copy">创建后会生成一个独立的报告任务。你可以在任务中心同时观察初筛和报告，不需要停留在当前页面。</div>
          <NButton type="primary" @click="submitReport">
            <template #icon>
              <FileText :size="16" />
            </template>
            创建简洁报告任务
          </NButton>
        </div>
      </NCard>

      <NCard title="筛选记录" class="panel-surface">
        <ScreeningRecordsTable :rows="task.records" />
      </NCard>
    </template>

    <template v-if="task.kind === 'report'">
      <MarkdownArticle v-if="task.markdown_preview" :source="task.markdown_preview" />
      <NAlert v-else type="info" :show-icon="false">
        报告任务已创建。完成后这里会直接显示 Markdown 预览。
      </NAlert>
    </template>

    <NCard title="产物文件" class="panel-surface">
      <ArtifactList :task-id="task.id" :artifacts="task.artifacts" />
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
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
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

.error-block {
  white-space: pre-wrap;
  margin: 0;
  font-family: Consolas, monospace;
}

@media (max-width: 1100px) {
  .task-hero,
  .report-action-row {
    flex-direction: column;
    align-items: stretch;
  }

  .metrics-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
