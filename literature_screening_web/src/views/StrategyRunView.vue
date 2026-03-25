<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Sparkles } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NCheckbox,
  NForm,
  NFormItem,
  NGrid,
  NGridItem,
  NInput,
  NInputNumber,
  NSelect,
  NSpace,
  useMessage
} from 'naive-ui'
import { useDraftsStore } from '@/stores/drafts'
import { useMetaStore } from '@/stores/meta'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import type { ModelSettings, ProviderName, StrategyDatabase } from '@/types/api'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const metaStore = useMetaStore()
const projectsStore = useProjectsStore()
const tasksStore = useTasksStore()
const draftsStore = useDraftsStore()

const selectedProjectId = ref<string | null>(null)
const newProjectName = ref('')
const newProjectDescription = ref('')
const title = ref('new-search-strategy')
const projectTopic = ref('')
const researchNeed = ref('')
const selectedDatabases = ref<StrategyDatabase[]>(['scopus', 'wos', 'pubmed', 'cnki'])
const provider = ref<ProviderName>('deepseek')
const model = ref<ModelSettings>({
  provider: 'deepseek',
  model_name: 'deepseek-reasoner',
  api_base_url: 'https://api.deepseek.com/v1',
  api_key_env: 'DEEPSEEK_API_KEY',
  api_key: '',
  temperature: 0,
  max_tokens: 4096,
  min_request_interval_seconds: 2
})
const retryTimes = ref(4)
const timeoutSeconds = ref(180)
const hydratingDraft = ref(false)

const projectOptions = computed(() =>
  projectsStore.list.map((item) => ({
    label: `${item.name} | ${item.topic}`,
    value: item.id
  }))
)

const strategyDatabaseOptions = computed(() =>
  metaStore.strategyDefaults.databases.map((item) => ({
    label: item.label,
    value: item.value as StrategyDatabase
  }))
)

const selectedPreset = computed(() => metaStore.providerPresets.find((item) => item.provider === provider.value))
const canSubmit = computed(
  () =>
    Boolean((selectedProjectId.value || newProjectName.value.trim()) && projectTopic.value.trim() && researchNeed.value.trim()) &&
    selectedDatabases.value.length > 0
)

function toggleDatabase(database: StrategyDatabase, checked: boolean) {
  selectedDatabases.value = checked
    ? Array.from(new Set([...selectedDatabases.value, database]))
    : selectedDatabases.value.filter((item) => item !== database)
}

function applyDraft() {
  const draft = draftsStore.strategyDraft
  selectedProjectId.value = draft.projectId
  newProjectName.value = draft.newProjectName
  newProjectDescription.value = draft.newProjectDescription
  title.value = draft.title
  projectTopic.value = draft.projectTopic
  researchNeed.value = draft.researchNeed
  selectedDatabases.value = [...draft.selectedDatabases]
  retryTimes.value = draft.retryTimes
  timeoutSeconds.value = draft.timeoutSeconds
}

function persistDraft() {
  draftsStore.updateStrategyDraft({
    projectId: selectedProjectId.value,
    newProjectName: newProjectName.value,
    newProjectDescription: newProjectDescription.value,
    title: title.value,
    projectTopic: projectTopic.value,
    researchNeed: researchNeed.value,
    selectedDatabases: selectedDatabases.value,
    retryTimes: retryTimes.value,
    timeoutSeconds: timeoutSeconds.value
  })
}

watch(
  [
    selectedProjectId,
    newProjectName,
    newProjectDescription,
    title,
    projectTopic,
    researchNeed,
    selectedDatabases,
    retryTimes,
    timeoutSeconds
  ],
  () => persistDraft(),
  { deep: true }
)

watch(selectedProjectId, async (nextProjectId) => {
  if (!nextProjectId) return
  const project = await projectsStore.loadProject(nextProjectId)
  if (!hydratingDraft.value && project && !projectTopic.value.trim()) {
    projectTopic.value = project.topic
  }
})

watch(provider, (nextProvider) => {
  const preset = metaStore.providerPresets.find((item) => item.provider === nextProvider)
  if (!preset) return
  model.value = {
    ...model.value,
    provider: preset.provider,
    model_name: nextProvider === 'deepseek' ? metaStore.strategyDefaults.model_name : preset.defaultModel,
    api_base_url: preset.defaultBaseUrl,
    api_key_env: preset.defaultApiKeyEnv,
    api_key: draftsStore.getProviderApiKey(preset.provider)
  }
})

async function submit() {
  const task = await tasksStore.submitStrategy({
    title: title.value.trim() || 'new-search-strategy',
    project_id: selectedProjectId.value,
    new_project_name: selectedProjectId.value ? '' : newProjectName.value.trim(),
    new_project_description: selectedProjectId.value ? '' : newProjectDescription.value.trim(),
    project_topic: projectTopic.value.trim(),
    research_need: researchNeed.value.trim(),
    selected_databases: selectedDatabases.value,
    retry_times: retryTimes.value,
    timeout_seconds: timeoutSeconds.value,
    model: model.value
  })
  draftsStore.clearStrategyDraft()
  message.success('检索与筛选方案任务已创建')
  if (task.project_id) {
    await router.push(`/threads/${task.project_id}`)
    return
  }
  await router.push(`/tasks/${task.id}`)
}

onMounted(async () => {
  draftsStore.hydrate()
  await Promise.all([metaStore.ensureLoaded(), projectsStore.refreshProjects()])
  hydratingDraft.value = true
  applyDraft()
  if (!model.value.api_key) {
    model.value.api_key = draftsStore.getProviderApiKey(provider.value)
  }

  const queryProjectId = typeof route.query.projectId === 'string' ? route.query.projectId : null
  if (queryProjectId) {
    selectedProjectId.value = queryProjectId
  }
  hydratingDraft.value = false

  if (selectedProjectId.value) {
    const project = await projectsStore.loadProject(selectedProjectId.value)
    if (project && !projectTopic.value.trim()) {
      projectTopic.value = project.topic
    }
  }
})
</script>

<template>
  <div class="strategy-view">
    <section class="strategy-hero panel-surface">
      <div>
        <div class="eyebrow">Search Strategy Composer</div>
        <h1>先把研究需求整理成检索词、数据库高级检索式和筛选标准</h1>
        <p>这个模块独立生成检索与筛选方案。生成结果会留在线程里，并可一键带入现有初筛模块。</p>
      </div>
      <NAlert type="info" :show-icon="false">
        当前默认使用 DeepSeek Reasoner 生成方案。支持四种检索输出：Scopus、Web of Science、PubMed 和知网。
      </NAlert>
    </section>

    <div class="strategy-grid">
      <NCard title="线程与主题" class="panel-surface">
        <NForm label-placement="top">
          <NFormItem label="选择已有主题线程">
            <NSelect
              v-model:value="selectedProjectId"
              clearable
              :options="projectOptions"
              placeholder="选择线程，或留空后新建线程"
            />
          </NFormItem>
          <NFormItem v-if="!selectedProjectId" label="新建线程名称">
            <NInput v-model:value="newProjectName" placeholder="例如：AI/XR 在猫咪与动物交互中的应用" />
          </NFormItem>
          <NFormItem v-if="!selectedProjectId" label="线程说明">
            <NInput v-model:value="newProjectDescription" placeholder="可选，用于记录委托背景和范围" />
          </NFormItem>
          <NFormItem label="研究主题">
            <NInput v-model:value="projectTopic" placeholder="用于线程主题和初筛主题的统一描述" />
          </NFormItem>
          <NFormItem label="任务名称">
            <NInput v-model:value="title" />
          </NFormItem>
        </NForm>
      </NCard>

      <NCard title="研究需求" class="panel-surface">
        <NForm label-placement="top">
          <NFormItem label="需求描述">
            <NInput
              v-model:value="researchNeed"
              type="textarea"
              :autosize="{ minRows: 14, maxRows: 22 }"
              placeholder="描述研究对象、技术方法、应用场景、重点指标、明显干扰词和排除方向。"
            />
          </NFormItem>
        </NForm>
      </NCard>

      <NCard title="输出数据库" class="panel-surface">
        <NForm label-placement="top">
          <NFormItem label="选择需要生成的检索式">
            <NSpace vertical>
              <NCheckbox
                v-for="option in strategyDatabaseOptions"
                :key="option.value"
                :checked="selectedDatabases.includes(option.value)"
                @update:checked="(checked) => toggleDatabase(option.value, checked)"
              >
                {{ option.label }}
              </NCheckbox>
            </NSpace>
          </NFormItem>
          <NAlert type="info" :show-icon="false">
            知网高级检索会按“篇关摘”格式生成，每行使用“关键词 + 关键词 + 关键词”，其中 + 表示同义词 OR。
          </NAlert>
        </NForm>
      </NCard>

      <NCard title="模型与执行" class="panel-surface">
        <NForm label-placement="top">
          <NFormItem label="模型提供商">
            <NSelect
              v-model:value="provider"
              :options="metaStore.providerPresets.map((item) => ({ label: item.label, value: item.provider }))"
            />
          </NFormItem>
          <NFormItem label="默认模型">
            <NInput :value="selectedPreset?.label || '-'" disabled />
          </NFormItem>
          <NFormItem label="模型名称">
            <NInput v-model:value="model.model_name" />
          </NFormItem>
          <NFormItem label="API Key 变量名">
            <NInput v-model:value="model.api_key_env" placeholder="例如：DEEPSEEK_API_KEY" />
          </NFormItem>
          <NFormItem label="API Key（本地缓存）">
            <NInput
              type="password"
              show-password-on="click"
              :value="model.api_key || ''"
              @update:value="(value) => { model.api_key = value; draftsStore.setProviderApiKey(provider, value) }"
              placeholder="可直接填写，仅保存在当前浏览器本地"
            />
          </NFormItem>
          <NGrid :cols="2" :x-gap="12" responsive="screen" item-responsive>
            <NGridItem span="1">
              <NFormItem label="重试次数">
                <NInputNumber v-model:value="retryTimes" :min="0" :max="8" />
              </NFormItem>
            </NGridItem>
            <NGridItem span="1">
              <NFormItem label="超时（秒）">
                <NInputNumber v-model:value="timeoutSeconds" :min="60" :max="300" />
              </NFormItem>
            </NGridItem>
          </NGrid>
        </NForm>
      </NCard>
    </div>

    <section class="action-bar panel-surface">
      <NButton type="primary" size="large" :disabled="!canSubmit || tasksStore.submitting" @click="submit">
        <template #icon>
          <Sparkles :size="16" />
        </template>
        生成检索与筛选方案
      </NButton>
      <NButton tertiary @click="router.push('/')">
        返回线程列表
      </NButton>
    </section>
  </div>
</template>

<style scoped>
.strategy-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.strategy-hero {
  padding: 22px 24px;
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 18px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 12px;
  color: #6a776c;
}

h1 {
  margin: 8px 0 12px;
}

p {
  margin: 0;
  color: #5b665d;
  line-height: 1.75;
}

.strategy-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 18px;
}

.check-row {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #334037;
}

.action-bar {
  padding: 18px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

@media (max-width: 1100px) {
  .strategy-hero,
  .strategy-grid {
    grid-template-columns: 1fr;
  }

  .action-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
}
</style>
