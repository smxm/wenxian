<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { FileOutput, FileText, LoaderCircle, RefreshCw } from 'lucide-vue-next'
import { NAlert, NButton, NCard, NDivider, NGrid, NGridItem, NInput, NInputNumber, NModal, NSelect, NSpace, NSpin, NText } from 'naive-ui'
import ArtifactList from '@/components/ArtifactList.vue'
import MarkdownArticle from '@/components/MarkdownArticle.vue'
import OverviewMetric from '@/components/OverviewMetric.vue'
import ScreeningRecordsTable from '@/components/ScreeningRecordsTable.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useMetaStore } from '@/stores/meta'
import { useTasksStore } from '@/stores/tasks'

const route = useRoute()
const router = useRouter()
const tasksStore = useTasksStore()
const metaStore = useMetaStore()

const reportModalOpen = ref(false)
const reportName = ref('simple_report')
const reportTitle = ref('report-task')
const reportTopic = ref('')
const reportReferenceStyle = ref<'gbt7714' | 'apa7'>('gbt7714')
const reportRetryTimes = ref(6)
const reportTimeout = ref(240)

const taskId = computed(() => String(route.params.taskId))
const task = computed(() => tasksStore.currentTask)
const isRunning = computed(() => task.value?.status === 'running' || task.value?.status === 'pending')
const isScreeningTask = computed(() => task.value?.kind === 'screening')
const screeningSummary = computed<Record<string, number | string>>(() => {
  const source = task.value?.summary ?? {}
  return {
    raw_entries_count: Number(source.raw_entries_count ?? 0),
    deduped_entries_count: Number(source.deduped_entries_count ?? 0),
    included_count: Number(source.included_count ?? 0),
    uncertain_count: Number(source.uncertain_count ?? 0)
  }
})

let pollTimer: number | null = null

function stopPolling() {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer)
    pollTimer = null
  }
}

function startPolling() {
  stopPolling()
  pollTimer = window.setInterval(async () => {
    if (!taskId.value) return
    const current = await tasksStore.loadTask(taskId.value)
    if (!current || (current.status !== 'running' && current.status !== 'pending')) {
      stopPolling()
    }
  }, 4000)
}

onMounted(async () => {
  await metaStore.ensureLoaded()
  const current = await tasksStore.loadTask(taskId.value)
  if (current?.project_topic) reportTopic.value = current.project_topic
  if (current && (current.status === 'running' || current.status === 'pending')) {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})

async function openReportModal() {
  reportTitle.value = `${task.value?.title || 'screening'}-report`
  reportTopic.value = task.value?.project_topic || ''
  reportModalOpen.value = true
}

async function submitReport() {
  if (!task.value) return
  const preset = metaStore.providerPresets.find(item => item.provider === 'deepseek') ?? metaStore.providerPresets[0]
  const created = await tasksStore.submitReport({
    title: reportTitle.value,
    screening_task_id: task.value.id,
    project_topic: reportTopic.value,
    report_name: reportName.value,
    retry_times: reportRetryTimes.value,
    timeout_seconds: reportTimeout.value,
    reference_style: reportReferenceStyle.value,
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
  reportModalOpen.value = false
  await router.push(`/tasks/${created.id}`)
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
          <NText depth="3">阶段：{{ task.phase }}</NText>
          <NText depth="3">更新时间：{{ dayjs(task.updated_at).format('YYYY-MM-DD HH:mm:ss') }}</NText>
        </div>
      </div>
      <NSpace>
        <NButton tertiary @click="tasksStore.loadTask(task.id)">
          <template #icon>
            <RefreshCw :size="16" />
          </template>
          刷新
        </NButton>
        <NButton v-if="isScreeningTask && task.status === 'succeeded'" type="primary" @click="openReportModal">
          <template #icon>
            <FileText :size="16" />
          </template>
          生成简洁报告
        </NButton>
      </NSpace>
    </section>

    <NAlert v-if="task.error" type="error" :show-icon="false">
      <pre class="error-block">{{ task.error }}</pre>
    </NAlert>

    <NSpin v-if="isRunning" size="large">
      <template #description>
        任务正在后台执行，页面会自动轮询最新状态。
      </template>
    </NSpin>

    <template v-if="task.kind === 'screening'">
      <section class="metrics-grid">
        <OverviewMetric label="原始条目" :value="screeningSummary.raw_entries_count ?? 0" />
        <OverviewMetric label="去重后" :value="screeningSummary.deduped_entries_count ?? 0" />
        <OverviewMetric label="纳入" :value="screeningSummary.included_count ?? 0" />
        <OverviewMetric label="不确定" :value="screeningSummary.uncertain_count ?? 0" />
      </section>

      <NCard title="筛选记录" class="panel-surface">
        <ScreeningRecordsTable :rows="task.records" />
      </NCard>
    </template>

    <template v-if="task.kind === 'report' && task.markdown_preview">
      <MarkdownArticle :source="task.markdown_preview" />
    </template>

    <NCard title="产物文件" class="panel-surface">
      <ArtifactList :task-id="task.id" :artifacts="task.artifacts" />
    </NCard>

    <NModal v-model:show="reportModalOpen" preset="card" title="生成简洁报告" style="max-width: 760px;">
      <NGrid :cols="2" :x-gap="16" :y-gap="10">
        <NGridItem span="2">
          <NInput v-model:value="reportTitle" placeholder="报告任务名称" />
        </NGridItem>
        <NGridItem span="2">
          <NInput v-model:value="reportTopic" placeholder="报告主题" />
        </NGridItem>
        <NGridItem span="2 m:1">
          <NInput v-model:value="reportName" placeholder="输出目录名" />
        </NGridItem>
        <NGridItem span="2 m:1">
          <NSelect
            v-model:value="reportReferenceStyle"
            :options="metaStore.referenceStyles.map(item => ({ label: item.label, value: item.value }))"
          />
        </NGridItem>
        <NGridItem span="2 m:1">
          <NInputNumber v-model:value="reportRetryTimes" :min="0" :max="10" />
        </NGridItem>
        <NGridItem span="2 m:1">
          <NInputNumber v-model:value="reportTimeout" :min="60" :max="600" />
        </NGridItem>
      </NGrid>

      <NDivider />
      <NSpace justify="end">
        <NButton @click="reportModalOpen = false">取消</NButton>
        <NButton type="primary" @click="submitReport">创建报告任务</NButton>
      </NSpace>
    </NModal>
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

.error-block {
  white-space: pre-wrap;
  margin: 0;
  font-family: Consolas, monospace;
}

@media (max-width: 1100px) {
  .task-hero {
    flex-direction: column;
  }

  .metrics-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
