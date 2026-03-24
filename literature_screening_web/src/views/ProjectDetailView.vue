<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import dayjs from 'dayjs'
import { FileSearch, FileText } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NEmpty,
  NForm,
  NFormItem,
  NGrid,
  NGridItem,
  NInput,
  NSelect,
  NSpace,
  NTag,
  NText,
  useMessage
} from 'naive-ui'
import StatusPill from '@/components/StatusPill.vue'
import { useDraftsStore } from '@/stores/drafts'
import { useMetaStore } from '@/stores/meta'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const projectsStore = useProjectsStore()
const tasksStore = useTasksStore()
const metaStore = useMetaStore()
const draftsStore = useDraftsStore()

const projectId = computed(() => String(route.params.projectId))
const datasetQuery = ref('')
const datasetKindFilter = ref<string | null>(null)
const taskQuery = ref('')
const reportTitle = ref('project-report')
const reportTopic = ref('')
const reportName = ref('project_report')
const reportDatasetIds = ref<string[]>([])
const reportReferenceStyle = ref<'gbt7714' | 'apa7'>('gbt7714')

const project = computed(() => projectsStore.currentProject)

const filteredDatasets = computed(() => {
  const query = datasetQuery.value.trim().toLowerCase()
  const datasets = project.value?.datasets ?? []
  return datasets.filter((item) => {
    if (datasetKindFilter.value && item.kind !== datasetKindFilter.value) return false
    if (!query) return true
    return [item.label, item.filename, item.kind].some((value) => value.toLowerCase().includes(query))
  })
})

const filteredTasks = computed(() => {
  const query = taskQuery.value.trim().toLowerCase()
  const tasks = project.value?.tasks ?? []
  if (!query) return tasks
  return tasks.filter((item) =>
    [item.title, item.phase, item.project_topic ?? '', item.parent_task_id ?? ''].some((value) =>
      value.toLowerCase().includes(query)
    )
  )
})

const reportDatasetOptions = computed(() =>
  (project.value?.datasets ?? [])
    .filter((item) => ['included', 'cumulative_included'].includes(item.kind))
    .map((item) => ({
      label: `${item.label} · ${item.record_count ?? '-'} 篇 · ${item.kind}`,
      value: item.id
    }))
)

onMounted(async () => {
  await metaStore.ensureLoaded()
  const loaded = await projectsStore.loadProject(projectId.value)
  reportTopic.value = loaded?.topic ?? ''
  reportTitle.value = `${loaded?.name ?? 'project'}-report`
  const cumulative = loaded?.datasets.find((item) => item.kind === 'cumulative_included')
  if (cumulative) {
    reportDatasetIds.value = [cumulative.id]
  }
})

async function submitProjectReport() {
  if (!project.value || !reportDatasetIds.value.length) return
  const preset = metaStore.providerPresets.find((item) => item.provider === 'deepseek') ?? metaStore.providerPresets[0]
  const task = await tasksStore.submitReport({
    title: reportTitle.value,
    screening_task_id: null,
    dataset_ids: reportDatasetIds.value,
    project_topic: reportTopic.value,
    report_name: reportName.value,
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
  message.success('项目报告任务已创建')
  await router.push(`/tasks/${task.id}`)
}
</script>

<template>
  <div class="project-detail-view" v-if="project">
    <section class="hero panel-surface">
      <div>
        <div class="eyebrow">Project</div>
        <h1>{{ project.name }}</h1>
        <p>{{ project.topic }}</p>
      </div>
      <NSpace>
        <RouterLink :to="{ path: '/screening/new', query: { projectId: project.id } }">
          <NButton type="primary">
            <template #icon>
              <FileSearch :size="16" />
            </template>
            新建项目初筛
          </NButton>
        </RouterLink>
      </NSpace>
    </section>

    <section class="grid-two">
      <NCard title="数据集" class="panel-surface">
        <div class="toolbar toolbar-grid">
          <NInput v-model:value="datasetQuery" placeholder="搜索数据集" />
          <NSelect
            v-model:value="datasetKindFilter"
            clearable
            :options="[
              { label: '纳入', value: 'included' },
              { label: '剔除', value: 'excluded' },
              { label: '未使用', value: 'unused' },
              { label: '累计纳入', value: 'cumulative_included' }
            ]"
            placeholder="数据集类型"
          />
        </div>
        <div v-if="filteredDatasets.length" class="stack-list">
          <div v-for="dataset in filteredDatasets" :key="dataset.id" class="dataset-item">
            <div>
              <div class="item-title">{{ dataset.label }}</div>
              <div class="item-meta">
                <NTag size="small">{{ dataset.kind }}</NTag>
                <span>{{ dataset.filename }}</span>
                <span v-if="dataset.record_count !== null && dataset.record_count !== undefined">· {{ dataset.record_count }} 篇</span>
              </div>
              <div v-if="dataset.source_dataset_ids.length" class="item-submeta">
                来源数据集：{{ dataset.source_dataset_ids.join('，') }}
              </div>
            </div>
            <NSpace>
              <RouterLink
                :to="{ path: '/screening/new', query: { projectId: project.id, sourceDatasetId: dataset.id, parentTaskId: dataset.task_id || undefined } }"
              >
                <NButton size="small" tertiary>继续筛选</NButton>
              </RouterLink>
            </NSpace>
          </div>
        </div>
        <NEmpty v-else description="当前项目还没有可用数据集。" />
      </NCard>

      <NCard title="项目报告" class="panel-surface">
        <NForm label-placement="top">
          <NFormItem label="报告任务名称">
            <NInput v-model:value="reportTitle" />
          </NFormItem>
          <NFormItem label="报告主题">
            <NInput v-model:value="reportTopic" />
          </NFormItem>
          <NGrid :cols="2" :x-gap="12">
            <NGridItem>
              <NFormItem label="来源数据集">
                <NSelect v-model:value="reportDatasetIds" multiple :options="reportDatasetOptions" />
              </NFormItem>
            </NGridItem>
            <NGridItem>
              <NFormItem label="参考样式">
                <NSelect
                  v-model:value="reportReferenceStyle"
                  :options="metaStore.referenceStyles.map((item) => ({ label: item.label, value: item.value }))"
                />
              </NFormItem>
            </NGridItem>
          </NGrid>
          <NFormItem label="输出目录名">
            <NInput v-model:value="reportName" />
          </NFormItem>
        </NForm>
        <NAlert type="info" :show-icon="false">
          如果你想基于多轮筛选的累计结果生成报告，优先选择 <code>cumulative_included</code> 数据集。
        </NAlert>
        <div class="action-spacer" />
        <NButton type="primary" :disabled="!reportDatasetIds.length" @click="submitProjectReport">
          <template #icon>
            <FileText :size="16" />
          </template>
          基于所选数据集生成报告
        </NButton>
      </NCard>
    </section>

    <NCard title="任务链" class="panel-surface">
      <div class="toolbar">
        <NInput v-model:value="taskQuery" placeholder="搜索任务" />
      </div>
      <div v-if="filteredTasks.length" class="stack-list">
        <RouterLink v-for="task in filteredTasks" :key="task.id" :to="`/tasks/${task.id}`" class="task-item">
          <div>
            <div class="item-title">{{ task.title }}</div>
            <div class="item-meta">
              <span>{{ task.kind === 'screening' ? '初筛任务' : '报告任务' }}</span>
              <span>· {{ task.phase_label || task.phase }}</span>
              <span>· {{ dayjs(task.updated_at).format('YYYY-MM-DD HH:mm:ss') }}</span>
              <span v-if="task.parent_task_id">· 父任务 {{ task.parent_task_id }}</span>
            </div>
          </div>
          <StatusPill :status="task.status" />
        </RouterLink>
      </div>
      <NEmpty v-else description="当前项目还没有任务。" />
    </NCard>
  </div>
</template>

<style scoped>
.project-detail-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  padding: 24px;
}

.eyebrow {
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
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.toolbar {
  margin-bottom: 12px;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 12px;
}

.stack-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dataset-item,
.task-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: 14px 0;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.dataset-item:first-child,
.task-item:first-child {
  border-top: none;
  padding-top: 0;
}

.item-title {
  font-weight: 700;
}

.item-meta,
.item-submeta {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: #5b665d;
  font-size: 13px;
}

.action-spacer {
  height: 12px;
}

@media (max-width: 1100px) {
  .hero,
  .grid-two,
  .toolbar-grid {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}
</style>
