<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import dayjs from 'dayjs'
import { ArrowRight, Bot, FilePlus2, FolderOpenDot, Pencil, Sparkles, Trash2 } from 'lucide-vue-next'
import { NButton, NCard, NEmpty, NForm, NFormItem, NInput, NModal, NSpace, NTag, useMessage } from 'naive-ui'
import OverviewMetric from '@/components/OverviewMetric.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useDraftsStore } from '@/stores/drafts'
import { useMetaStore } from '@/stores/meta'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'

const router = useRouter()
const message = useMessage()
const metaStore = useMetaStore()
const tasksStore = useTasksStore()
const draftsStore = useDraftsStore()
const projectsStore = useProjectsStore()

const showCreateModal = ref(false)

const createForm = reactive({
  title: '',
  content: ''
})

const editingProjectId = ref<string | null>(null)
const editForm = reactive({
  name: '',
  topic: '',
  description: ''
})

const stats = computed(() => {
  const tasks = tasksStore.list
  return {
    threads: projectsStore.list.length,
    running: tasks.filter((task) => task.status === 'running' || task.status === 'pending').length,
    screening: tasks.filter((task) => task.kind === 'screening').length,
    reports: tasks.filter((task) => task.kind === 'report').length
  }
})

const threadCards = computed(() =>
  projectsStore.list.map((project) => {
    const relatedTasks = tasksStore.list.filter((task) => task.project_id === project.id)
    return {
      ...project,
      screeningCount: relatedTasks.filter((task) => task.kind === 'screening').length,
      reportCount: relatedTasks.filter((task) => task.kind === 'report').length,
      running: relatedTasks.some((task) => task.status === 'running' || task.status === 'pending'),
      latestTask: relatedTasks[0] ?? null
    }
  })
)

function resetCreateForm() {
  createForm.title = ''
  createForm.content = ''
}

async function createThread() {
  if (!createForm.title.trim() || !createForm.content.trim()) {
    message.warning('主题和内容不能为空')
    return
  }
  const project = await projectsStore.createProject({
    name: createForm.title.trim(),
    topic: createForm.content.trim(),
    description: createForm.content.trim()
  })
  resetCreateForm()
  showCreateModal.value = false
  message.success('主题线程已创建')
  await router.push(`/threads/${project.id}`)
}

function openEditThread(project: { id: string; name: string; topic: string; description: string }) {
  editingProjectId.value = project.id
  editForm.name = project.name
  editForm.topic = project.topic
  editForm.description = project.description ?? ''
}

async function saveThreadEdit() {
  if (!editingProjectId.value) return
  if (!editForm.name.trim() || !editForm.topic.trim()) {
    message.warning('主题和内容不能为空')
    return
  }
  await projectsStore.updateProject(editingProjectId.value, {
    name: editForm.name.trim(),
    topic: editForm.topic.trim(),
    description: editForm.description.trim()
  })
  editingProjectId.value = null
  message.success('主题线程已更新')
}

async function removeThread(project: { id: string; name: string }) {
  if (!window.confirm(`确认删除主题“${project.name}”？相关初筛和报告任务也会一起删除。`)) {
    return
  }
  await projectsStore.deleteProject(project.id)
  await tasksStore.refreshList()
  message.success('主题线程已删除')
}

onMounted(async () => {
  draftsStore.hydrate()
  await Promise.all([metaStore.ensureLoaded(), tasksStore.refreshList(), projectsStore.refreshProjects()])
})
</script>

<template>
  <div class="view-stack">
    <section class="hero-grid">
      <div class="hero-copy panel-surface">
        <div class="eyebrow">Thread-first Workflow</div>
        <h1>按主题建立线程，在同一条线里推进检索方案、初筛、复核和报告</h1>
        <p>
          这里不再要求先理解项目、数据集或任务类型。先建一个主题线程，在线程里逐步新增初筛轮次、
          基于剩余文献继续筛选，最后生成报告。
        </p>
        <NSpace>
          <NButton type="primary" size="large" @click="showCreateModal = true">
            <template #icon>
              <FilePlus2 :size="16" />
            </template>
            新建线程
          </NButton>
          <RouterLink to="/screening/new">
            <NButton secondary size="large">
              {{ draftsStore.hasScreeningDraft ? '继续未提交的初筛草稿' : '打开高级初筛入口' }}
              <template #icon>
                <ArrowRight :size="16" />
              </template>
            </NButton>
          </RouterLink>
          <RouterLink to="/strategy/new">
            <NButton tertiary size="large">
              <template #icon>
                <Sparkles :size="16" />
              </template>
              生成检索与筛选方案
            </NButton>
          </RouterLink>
        </NSpace>
      </div>

      <div class="hero-side panel-surface">
        <div class="hero-side-title">当前能力</div>
        <div class="support-grid">
          <div class="support-item">
            <FolderOpenDot :size="18" />
            <span>{{ metaStore.acceptedInputFormats.join(' / ') || '.bib / .ris / .enw / .txt' }}</span>
          </div>
          <div class="support-item">
            <Bot :size="18" />
            <span>{{ metaStore.providerPresets.map((item) => item.label).join(' / ') || 'DeepSeek / Kimi' }}</span>
          </div>
          <div class="support-item">
            <Sparkles :size="18" />
            <span>线程内可继续筛剩余文献、人工复核，并基于复核结果直接生成报告</span>
          </div>
        </div>
      </div>
    </section>

    <section class="metric-grid">
      <OverviewMetric label="主题线程" :value="stats.threads" />
      <OverviewMetric label="运行中任务" :value="stats.running" />
      <OverviewMetric label="初筛轮次" :value="stats.screening" />
      <OverviewMetric label="报告任务" :value="stats.reports" />
    </section>

    <section class="dashboard-grid">
      <NCard title="如何使用" class="panel-surface">
        <ol class="principles">
          <li>先新建一个主题线程，只填主题和内容说明。</li>
          <li>进入线程后，按需要先生成检索与筛选方案，或直接发起第一轮初筛。</li>
          <li>每一轮初筛完成后，都能继续筛未使用文献、进入人工复核或直接生成报告。</li>
          <li>报告和复核结果都会回到同一条线程里，不需要单独管理底层数据集。</li>
        </ol>
      </NCard>

      <NCard title="最近主题线程" class="panel-surface">
        <div v-if="threadCards.length" class="thread-list">
          <RouterLink v-for="thread in threadCards" :key="thread.id" :to="`/threads/${thread.id}`" class="thread-card">
            <div class="thread-card-header">
              <div class="thread-card-title">{{ thread.name }}</div>
              <div class="thread-card-actions">
                <StatusPill :status="thread.running ? 'running' : (thread.latestTask?.status ?? 'succeeded')" />
                <NButton quaternary circle size="small" @click.prevent="openEditThread(thread)">
                  <template #icon>
                    <Pencil :size="14" />
                  </template>
                </NButton>
                <NButton quaternary circle size="small" @click.prevent="removeThread(thread)">
                  <template #icon>
                    <Trash2 :size="14" />
                  </template>
                </NButton>
              </div>
            </div>
            <div class="thread-card-topic">{{ thread.topic }}</div>
            <div class="thread-card-meta">
              <NTag size="small" round>{{ thread.screeningCount }} 轮初筛</NTag>
              <NTag size="small" round>{{ thread.reportCount }} 个报告</NTag>
              <span>更新于 {{ dayjs(thread.updated_at).format('YYYY-MM-DD HH:mm') }}</span>
            </div>
            <div class="thread-card-tail" v-if="thread.latestTask">最近动作：{{ thread.latestTask.title }}</div>
          </RouterLink>
        </div>
        <NEmpty v-else description="还没有主题线程" />
      </NCard>
    </section>

    <NModal
      :show="showCreateModal"
      preset="card"
      style="max-width: 720px"
      title="新建主题线程"
      @update:show="(value) => { showCreateModal = value; if (!value) resetCreateForm() }"
    >
      <NForm label-placement="top">
        <NFormItem label="主题">
          <NInput
            v-model:value="createForm.title"
            placeholder="例如：机器学习在场地效应（Site Effects）评估与预测中的应用"
          />
        </NFormItem>
        <NFormItem label="内容">
          <NInput
            v-model:value="createForm.content"
            type="textarea"
            :autosize="{ minRows: 5, maxRows: 10 }"
            placeholder="简要说明这条线程要解决什么问题、筛什么文献、最后要形成什么交付。"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showCreateModal = false">取消</NButton>
          <NButton type="primary" @click="createThread">创建线程</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      :show="editingProjectId !== null"
      preset="card"
      style="max-width: 720px"
      title="编辑主题线程"
      @update:show="(value) => { if (!value) editingProjectId = null }"
    >
      <NForm label-placement="top">
        <NFormItem label="主题">
          <NInput v-model:value="editForm.name" />
        </NFormItem>
        <NFormItem label="内容">
          <NInput v-model:value="editForm.topic" type="textarea" :autosize="{ minRows: 5, maxRows: 10 }" />
        </NFormItem>
        <NFormItem label="备注">
          <NInput v-model:value="editForm.description" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="editingProjectId = null">取消</NButton>
          <NButton type="primary" @click="saveThreadEdit">保存</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.view-stack {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-grid,
.dashboard-grid,
.metric-grid {
  display: grid;
  gap: 18px;
}

.hero-grid {
  grid-template-columns: 1.45fr 1fr;
}

.metric-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.dashboard-grid {
  grid-template-columns: 0.9fr 1.1fr;
}

.hero-copy,
.hero-side {
  padding: 24px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 12px;
  color: #6a776c;
}

.hero-side-title {
  font-weight: 700;
}

h1 {
  margin: 10px 0 14px;
  font-size: 38px;
  line-height: 1.08;
}

p {
  margin: 0 0 18px;
  color: #526055;
  line-height: 1.7;
}

.support-grid {
  display: grid;
  gap: 12px;
  margin-top: 12px;
}

.support-item {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 16px;
}

.principles {
  margin: 0;
  padding-left: 18px;
  color: #4e5b51;
  line-height: 1.8;
}

.thread-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.thread-card {
  display: block;
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.thread-card-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.thread-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.thread-card-title {
  font-size: 18px;
  font-weight: 700;
}

.thread-card-topic {
  margin-top: 10px;
  color: #526055;
  line-height: 1.7;
}

.thread-card-meta {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: #6a776c;
  font-size: 13px;
}

.thread-card-tail {
  margin-top: 12px;
  color: #3d4b40;
}

@media (max-width: 1100px) {
  .hero-grid,
  .dashboard-grid,
  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
