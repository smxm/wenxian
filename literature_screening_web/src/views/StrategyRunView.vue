<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Bot, Sparkles } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NCheckbox,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSpace,
  NTag,
  useMessage
} from 'naive-ui'
import { useDraftsStore } from '@/stores/drafts'
import { useMetaStore } from '@/stores/meta'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import type { ModelSettings, ProjectDetail, ProviderName, StrategyDatabase } from '@/types/api'

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
const draftNoticeDismissed = ref(false)
const routeProjectId = computed(() => {
  if (typeof route.params.projectId === 'string') return route.params.projectId
  if (typeof route.query.projectId === 'string') return route.query.projectId
  return null
})

const currentProject = computed<ProjectDetail | null>(() =>
  projectsStore.currentProject?.id === selectedProjectId.value ? projectsStore.currentProject : null
)

const isThreadScoped = computed(() => Boolean(routeProjectId.value))
const threadHomePath = computed(() => (selectedProjectId.value ? `/threads/${selectedProjectId.value}` : null))
const pageMode = computed(() => (isThreadScoped.value ? 'update' : 'create'))
const pageTitle = computed(() =>
  pageMode.value === 'update' ? '更新线程方案' : '输入研究需求，自动生成线程主题、筛选标准和检索式'
)
const pageCopy = computed(() =>
  pageMode.value === 'update'
    ? '你现在正在当前线程里刷新方案，不需要再次选择线程。新的主题、筛选标准和检索式会直接写回线程主页。'
    : '新线程不再要求你先手写主题和标准。只描述需求，系统会先生成检索式、主题和筛选标准，再把它们变成整条线程的默认上下文。'
)

const strategyDatabaseOptions = computed(() =>
  metaStore.strategyDefaults.databases.map((item) => ({
    label: item.label,
    value: item.value as StrategyDatabase
  }))
)

const selectedPreset = computed(() => metaStore.providerPresets.find((item) => item.provider === provider.value))
const canSubmit = computed(
  () => Boolean(researchNeed.value.trim()) && (isThreadScoped.value ? Boolean(selectedProjectId.value) : true) && selectedDatabases.value.length > 0
)

function toggleDatabase(database: StrategyDatabase, checked: boolean) {
  selectedDatabases.value = checked
    ? Array.from(new Set([...selectedDatabases.value, database]))
    : selectedDatabases.value.filter((item) => item !== database)
}

function restoreDraft() {
  const draft = draftsStore.strategyDraft
  selectedProjectId.value = routeProjectId.value
  newProjectName.value = routeProjectId.value ? '' : draft.newProjectName
  newProjectDescription.value = routeProjectId.value ? '' : draft.newProjectDescription
  researchNeed.value = draft.researchNeed
  selectedDatabases.value = [...draft.selectedDatabases]
  retryTimes.value = draft.retryTimes
  timeoutSeconds.value = draft.timeoutSeconds
  draftNoticeDismissed.value = true
}

function discardDraft() {
  draftsStore.clearStrategyDraft()
  draftNoticeDismissed.value = true
}

function persistDraft() {
  draftsStore.updateStrategyDraft({
    projectId: selectedProjectId.value,
    newProjectName: newProjectName.value,
    newProjectDescription: newProjectDescription.value,
    title: buildTaskTitle(),
    projectTopic: currentProject.value?.thread_profile?.screening.topic ?? '',
    researchNeed: researchNeed.value,
    selectedDatabases: selectedDatabases.value,
    retryTimes: retryTimes.value,
    timeoutSeconds: timeoutSeconds.value
  })
}

function applyProjectProfile(project: ProjectDetail) {
  const profile = project.thread_profile
  if (!profile) return
  if (!researchNeed.value.trim() && profile.strategy.research_need) {
    researchNeed.value = profile.strategy.research_need
  }
  if (profile.strategy.selected_databases.length) {
    selectedDatabases.value = [...profile.strategy.selected_databases]
  }
  if (profile.strategy.model) {
    model.value = {
      ...model.value,
      ...profile.strategy.model,
      api_key: draftsStore.getProviderApiKey(profile.strategy.model.provider)
    }
    provider.value = profile.strategy.model.provider
  }
}

function buildTaskTitle() {
  if (selectedProjectId.value && currentProject.value) {
    return `${currentProject.value.name}-thread-plan`
  }
  const explicitName = newProjectName.value.trim()
  if (explicitName) return `${explicitName}-thread-plan`
  const snippet = researchNeed.value.trim().slice(0, 24)
  return snippet ? `${snippet}-thread-plan` : 'new-thread-plan'
}

watch(
  [selectedProjectId, newProjectName, newProjectDescription, researchNeed, selectedDatabases, retryTimes, timeoutSeconds],
  () => persistDraft(),
  { deep: true }
)

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

watch(selectedProjectId, async (nextProjectId, previousProjectId) => {
  if (!isThreadScoped.value) return
  if (!nextProjectId) {
    if (previousProjectId) {
      newProjectName.value = ''
      newProjectDescription.value = ''
    }
    return
  }
  const project = await projectsStore.loadProject(nextProjectId)
  if (project && !hydratingDraft.value) {
    applyProjectProfile(project)
  }
})

async function submit() {
  const task = await tasksStore.submitStrategy({
    title: buildTaskTitle(),
    project_id: selectedProjectId.value,
    new_project_name: isThreadScoped.value ? '' : newProjectName.value.trim(),
    new_project_description: isThreadScoped.value ? '' : newProjectDescription.value.trim(),
    project_topic: currentProject.value?.thread_profile?.screening.topic ?? '',
    research_need: researchNeed.value.trim(),
    selected_databases: selectedDatabases.value,
    retry_times: retryTimes.value,
    timeout_seconds: timeoutSeconds.value,
    model: model.value
  })
  draftsStore.clearStrategyDraft()
  message.success(pageMode.value === 'update' ? '线程方案刷新任务已创建' : '线程方案生成任务已创建')
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
  if (!model.value.api_key) {
    model.value.api_key = draftsStore.getProviderApiKey(provider.value)
  }

  if (routeProjectId.value) {
    selectedProjectId.value = routeProjectId.value
    const project = await projectsStore.loadProject(routeProjectId.value)
    if (project) {
      newProjectName.value = project.name
      newProjectDescription.value = project.description ?? ''
      applyProjectProfile(project)
    }
  }
  hydratingDraft.value = false
})
</script>

<template>
  <div class="strategy-view">
    <section class="strategy-hero panel-surface">
      <div>
        <div class="eyebrow">Thread Kickoff</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageCopy }}</p>
      </div>
      <div class="hero-actions">
        <RouterLink v-if="threadHomePath" :to="threadHomePath">
          <NButton tertiary>
            <template #icon><ArrowLeft :size="16" /></template>
            返回线程主页
          </NButton>
        </RouterLink>
        <NAlert type="info" :show-icon="false">
          生成后会更新当前线程的主题、标准和检索式。
        </NAlert>
      </div>
    </section>

    <div class="strategy-grid">
      <NCard :title="pageMode === 'update' ? '当前线程' : '线程归属'" class="panel-surface">
        <template v-if="pageMode === 'update'">
          <div v-if="currentProject" class="thread-summary-block">
            <div class="thread-summary-title">{{ currentProject.name }}</div>
            <div class="thread-summary-copy">{{ currentProject.description || '当前线程会承接这次方案。' }}</div>
            <div class="thread-summary">
              <NTag round size="small">当前主题：{{ currentProject.thread_profile?.screening.topic || currentProject.topic }}</NTag>
              <NTag round size="small" type="success">已有 {{ currentProject.tasks.filter((task) => task.kind === 'screening').length }} 轮初筛</NTag>
            </div>
          </div>
          <NAlert v-else type="info" :show-icon="false">正在读取当前线程信息…</NAlert>
        </template>
        <NForm v-else label-placement="top">
          <NFormItem label="线程名称">
            <NInput
              v-model:value="newProjectName"
              placeholder="可选，不填会自动生成"
            />
          </NFormItem>
          <NFormItem label="线程备注">
            <NInput
              v-model:value="newProjectDescription"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 5 }"
              placeholder="可选"
            />
          </NFormItem>
        </NForm>
        <NAlert v-if="pageMode === 'create'" type="info" :show-icon="false" class="thread-help-alert">
          新线程会在这里创建。
        </NAlert>
        <div v-if="pageMode === 'create' && draftsStore.hasStrategyDraft && !draftNoticeDismissed" class="draft-restore-block">
          <NAlert type="warning" :show-icon="false">
            发现未提交草稿。
          </NAlert>
          <div class="draft-restore-actions">
            <NButton tertiary @click="restoreDraft">恢复旧草稿</NButton>
            <NButton tertiary @click="discardDraft">清空旧草稿</NButton>
          </div>
        </div>
      </NCard>

      <NCard title="研究需求" class="panel-surface card-span-2">
        <NForm label-placement="top">
          <NFormItem label="直接描述你要研究什么">
            <NInput
              v-model:value="researchNeed"
              type="textarea"
              :autosize="{ minRows: 12, maxRows: 18 }"
              placeholder="直接描述你的研究需求"
            />
          </NFormItem>
        </NForm>
      </NCard>

      <NCard title="方案生成设置" class="panel-surface">
        <NForm label-placement="top">
          <NFormItem label="模型提供商">
            <NSelect
              v-model:value="provider"
              :options="metaStore.providerPresets.map((item) => ({ label: item.label, value: item.provider }))"
            />
          </NFormItem>
          <NFormItem label="模型名称">
            <NInput v-model:value="model.model_name" />
          </NFormItem>
          <NFormItem label="API Key">
            <NInput
              type="password"
              show-password-on="click"
              :value="model.api_key || ''"
              @update:value="(value) => { model.api_key = value; draftsStore.setProviderApiKey(provider, value) }"
              placeholder="仅保存在当前浏览器本地"
            />
          </NFormItem>
        </NForm>

        <div class="setting-note">
          <Bot :size="16" />
          <span>{{ selectedPreset?.label || '当前模型' }} 会负责生成主题、筛选标准和检索式。</span>
        </div>
      </NCard>

      <NCard title="需要生成哪些数据库检索式" class="panel-surface">
        <div class="database-list">
          <label
            v-for="option in strategyDatabaseOptions"
            :key="option.value"
            class="database-option"
            :class="{ active: selectedDatabases.includes(option.value) }"
          >
            <NCheckbox
              :checked="selectedDatabases.includes(option.value)"
              @update:checked="(checked) => toggleDatabase(option.value, checked)"
            />
            <span>{{ option.label }}</span>
          </label>
        </div>
      </NCard>
    </div>

    <div class="action-bar panel-surface">
      <div>
        <div class="action-title">{{ pageMode === 'update' ? '刷新线程方案' : '创建线程并生成方案' }}</div>
        <div class="action-copy">
          会生成检索词、主题和筛选标准。
        </div>
      </div>
      <NSpace>
        <RouterLink v-if="threadHomePath" :to="threadHomePath">
          <NButton tertiary>返回线程</NButton>
        </RouterLink>
        <NButton :disabled="!canSubmit || tasksStore.submitting" type="primary" size="large" @click="submit">
          <template #icon>
            <Sparkles :size="16" />
          </template>
          {{ pageMode === 'update' ? '更新线程方案' : '创建线程' }}
        </NButton>
      </NSpace>
    </div>
  </div>
</template>

<style scoped>
.strategy-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.strategy-hero,
.action-bar {
  padding: 24px;
}

.hero-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.strategy-grid {
  display: grid;
  grid-template-columns: 1.05fr 1.15fr;
  gap: 18px;
}

.card-span-2 {
  grid-column: span 2;
}

.thread-summary {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.thread-summary-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.thread-summary-title,
.action-title {
  font-weight: 700;
}

.thread-summary-copy,
.action-copy {
  color: #5b665d;
}

.thread-help-alert {
  margin-top: 14px;
}

.draft-restore-block {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.draft-restore-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.database-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.database-option {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(63, 95, 74, 0.12);
  background: rgba(248, 250, 247, 0.88);
  cursor: pointer;
}

.database-option.active {
  border-color: rgba(45, 106, 79, 0.26);
  background: rgba(232, 242, 234, 0.96);
}

.setting-note {
  display: flex;
  gap: 8px;
  align-items: center;
  color: #5b665d;
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.action-title {
  margin-bottom: 4px;
}

@media (max-width: 960px) {
  .strategy-grid {
    grid-template-columns: 1fr;
  }

  .card-span-2 {
    grid-column: span 1;
  }

  .database-list {
    grid-template-columns: 1fr;
  }

  .action-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
