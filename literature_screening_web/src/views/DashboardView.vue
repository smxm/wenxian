<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import dayjs from 'dayjs'
import { ArrowRight, Bot, FolderOpenDot, MessageSquareText, Pencil, PlusCircle, Trash2 } from 'lucide-vue-next'
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

const createForm = reactive({
  name: '',
  topic: '',
  description: ''
})

const editingProjectId = reactive<{ value: string | null }>({ value: null })
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

async function createThread() {
  if (!createForm.name.trim() || !createForm.topic.trim()) {
    message.warning('主题名称和研究主题不能为空')
    return
  }
  const project = await projectsStore.createProject({
    name: createForm.name.trim(),
    topic: createForm.topic.trim(),
    description: createForm.description.trim()
  })
  createForm.name = ''
  createForm.topic = ''
  createForm.description = ''
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
    message.warning('Thread name and topic are required')
    return
  }
  await projectsStore.updateProject(editingProjectId.value, {
    name: editForm.name.trim(),
    topic: editForm.topic.trim(),
    description: editForm.description.trim()
  })
  editingProjectId.value = null
  message.success('Thread updated')
}

async function removeThread(project: { id: string; name: string }) {
  if (!window.confirm(`Delete thread "${project.name}"? This will also remove related screening and report tasks.`)) {
    return
  }
  await projectsStore.deleteProject(project.id)
  await tasksStore.refreshList()
  message.success('Thread deleted')
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
        <h1>按主题建立对话线程，在同一条线上持续推进多轮初筛与报告</h1>
        <p>一个主题就是一条长期线程。你可以在里面发起首轮筛选、从未使用文献继续下一轮、做人工复核，并最终生成报告。</p>
        <NSpace>
          <RouterLink to="/screening/new">
            <NButton type="primary" size="large">
              {{ draftsStore.hasScreeningDraft ? '继续未提交的初筛草稿' : '打开高级初筛入口' }}
              <template #icon>
                <ArrowRight :size="16" />
              </template>
            </NButton>
          </RouterLink>
          <RouterLink to="/tasks">
            <NButton tertiary size="large">查看后台任务</NButton>
          </RouterLink>
        </NSpace>
      </div>

      <div class="hero-side panel-surface">
        <div class="hero-side-title">当前环境</div>
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
            <MessageSquareText :size="18" />
            <span>线程里持续保存筛选轮次、人工修正和报告结果</span>
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
      <NCard title="新建主题线程" class="panel-surface">
        <NForm label-placement="top">
          <NFormItem label="主题线程名称">
            <NInput v-model:value="createForm.name" placeholder="例如：AI/XR 在猫咪与动物交互中的应用" />
          </NFormItem>
          <NFormItem label="研究主题">
            <NInput
              v-model:value="createForm.topic"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 6 }"
              placeholder="说明研究主题、交付目标或筛选范围"
            />
          </NFormItem>
          <NFormItem label="备注">
            <NInput
              v-model:value="createForm.description"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 4 }"
              placeholder="可选。记录委托背景、额外限制或后续说明"
            />
          </NFormItem>
        </NForm>
        <NButton type="primary" @click="createThread">
          <template #icon>
            <PlusCircle :size="16" />
          </template>
          创建主题线程
        </NButton>
      </NCard>

      <NCard title="线程说明" class="panel-surface">
        <ul class="principles">
          <li>每个主题线程可以包含多轮初筛，不同轮次自动串联。</li>
          <li>从上一轮未使用文献继续筛选，会直接成为线程中的下一条消息。</li>
          <li>报告生成、人工审核、参考列表修正都会回到同一条线程中。</li>
          <li>系统内部仍会跟踪文件和数据关系，但前端不再直接暴露 dataset 概念。</li>
        </ul>
      </NCard>
    </section>

    <section class="thread-grid">
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
            <div class="thread-card-tail" v-if="thread.latestTask">
              最近动作：{{ thread.latestTask.title }}
            </div>
          </RouterLink>
        </div>
        <NEmpty v-else description="还没有主题线程" />
      </NCard>
    </section>

    <NModal
      :show="editingProjectId.value !== null"
      preset="card"
      style="max-width: 640px"
      title="Edit Thread"
      @update:show="(value) => { if (!value) editingProjectId.value = null }"
    >
      <NForm label-placement="top">
        <NFormItem label="Thread Name">
          <NInput v-model:value="editForm.name" />
        </NFormItem>
        <NFormItem label="Topic">
          <NInput v-model:value="editForm.topic" type="textarea" :autosize="{ minRows: 3, maxRows: 6 }" />
        </NFormItem>
        <NFormItem label="Description">
          <NInput v-model:value="editForm.description" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="editingProjectId.value = null">Cancel</NButton>
          <NButton type="primary" @click="saveThreadEdit">Save</NButton>
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
.metric-grid,
.thread-grid {
  display: grid;
  gap: 18px;
}

.hero-grid {
  grid-template-columns: 1.5fr 1fr;
}

.metric-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.dashboard-grid {
  grid-template-columns: 1.2fr 1fr;
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
  font-size: 40px;
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
