<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import dayjs from 'dayjs'
import { ArrowRight, Bot, FolderOpenDot, MoreHorizontal } from 'lucide-vue-next'
import { NButton, NCard, NDropdown, NEmpty, NForm, NFormItem, NInput, NModal, NSpace, NTag, useMessage } from 'naive-ui'
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

const editingProjectId = ref<string | null>(null)
const editForm = reactive({
  name: '',
  topic: '',
  description: ''
})

const workflowSteps = [
  {
    step: '01',
    title: '研究需求',
    summary: '先创建线程。',
    detail: '后续再补主题、标准和方案。'
  },
  {
    step: '02',
    title: '线程内初筛',
    summary: '在线程里继续初筛。',
    detail: '每轮沿用当前主题和标准。'
  },
  {
    step: '03',
    title: '全文复核',
    summary: '处理候选文献。',
    detail: '标记获取状态和最终去留。'
  },
  {
    step: '04',
    title: '生成报告',
    summary: '从线程生成报告。',
    detail: '直接使用已纳入文献。'
  }
]

const threadActionOptions = [
  { label: '打开线程', key: 'open' },
  { label: '编辑主题', key: 'edit' },
  { type: 'divider', key: 'divider' },
  { label: '删除线程', key: 'delete' }
]

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
  [...projectsStore.list]
    .sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime())
    .map((project) => {
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

const featuredThreads = computed(() => threadCards.value.slice(0, 8))
const hiddenThreadCount = computed(() => Math.max(threadCards.value.length - featuredThreads.value.length, 0))
const workspaceSignals = computed(() => [
  { label: '主题线程', value: stats.value.threads, tone: 'emerald' },
  { label: '运行中任务', value: stats.value.running, tone: 'amber' },
  { label: '初筛轮次', value: stats.value.screening, tone: 'stone' },
  { label: '报告任务', value: stats.value.reports, tone: 'olive' }
])
const screeningEntryRoute = computed(() =>
  draftsStore.screeningDraft.projectId ? `/threads/${draftsStore.screeningDraft.projectId}/screening/new` : '/screening/new'
)

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

async function handleThreadAction(action: string, thread: { id: string; name: string; topic: string; description: string }) {
  if (action === 'open') {
    await router.push(`/threads/${thread.id}`)
    return
  }
  if (action === 'edit') {
    openEditThread(thread)
    return
  }
  if (action === 'delete') {
    await removeThread(thread)
  }
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
        <h1>先建线程，再继续初筛、复核和报告</h1>
        <p>输入研究需求创建线程，后续步骤都在线程里完成。</p>
        <div class="hero-actions">
          <RouterLink to="/threads/new">
            <NButton type="primary" size="large">
              新建线程
              <template #icon>
                <ArrowRight :size="16" />
              </template>
            </NButton>
          </RouterLink>
          <RouterLink :to="screeningEntryRoute">
            <NButton secondary size="large">
              {{ draftsStore.hasScreeningDraft ? '继续线程内初筛草稿' : '从已有线程继续初筛' }}
              <template #icon>
                <ArrowRight :size="16" />
              </template>
            </NButton>
          </RouterLink>
        </div>
        <div class="hero-flow">
          <div v-for="step in workflowSteps" :key="step.step" class="flow-card">
            <div class="flow-step">{{ step.step }}</div>
            <div class="flow-title">{{ step.title }}</div>
            <div class="flow-copy">{{ step.summary }}</div>
          </div>
        </div>
      </div>

      <div class="hero-side-stack">
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
              <span>主题、标准和检索式都会保存在同一条线程里</span>
            </div>
          </div>
        </div>

        <div class="hero-side panel-surface snapshot-panel">
          <div class="hero-side-title">工作台概览</div>
          <div class="snapshot-grid">
            <div
              v-for="signal in workspaceSignals"
              :key="signal.label"
              class="snapshot-item"
              :class="`snapshot-${signal.tone}`"
            >
              <div class="snapshot-label">{{ signal.label }}</div>
              <div class="snapshot-value">{{ signal.value }}</div>
            </div>
          </div>
          <div class="snapshot-note">
            {{ draftsStore.hasScreeningDraft ? '检测到未提交初筛草稿。' : '从新建线程开始，或继续最近线程。' }}
          </div>
        </div>
      </div>
    </section>

    <section class="dashboard-grid">
      <NCard title="默认流程" class="panel-surface">
        <div class="principle-grid">
          <div v-for="step in workflowSteps" :key="`${step.step}-detail`" class="principle-card">
            <div class="principle-step">{{ step.step }}</div>
            <div class="principle-title">{{ step.title }}</div>
            <div class="principle-copy">{{ step.detail }}</div>
          </div>
        </div>
        <div class="guide-note">
          线程页负责维护主题和标准。最近线程只显示最近一部分。
        </div>
      </NCard>

      <NCard title="最近主题线程" class="panel-surface">
        <div v-if="featuredThreads.length" class="thread-panel-head">
          <div class="thread-panel-copy">优先展示最近更新的线程，方便快速回到正在推进的任务。</div>
          <div class="thread-panel-meta">共 {{ threadCards.length }} 条线程</div>
        </div>
        <div v-if="featuredThreads.length" class="thread-grid">
          <RouterLink v-for="thread in featuredThreads" :key="thread.id" :to="`/threads/${thread.id}`" class="thread-card">
            <div class="thread-card-header">
              <div class="thread-card-title">{{ thread.name }}</div>
              <div class="thread-card-actions">
                <StatusPill :status="thread.running ? 'running' : (thread.latestTask?.status ?? 'succeeded')" />
                <NDropdown :options="threadActionOptions" trigger="click" @select="(key) => handleThreadAction(String(key), thread)">
                  <NButton quaternary circle size="small" @click.prevent>
                    <template #icon>
                      <MoreHorizontal :size="15" />
                    </template>
                  </NButton>
                </NDropdown>
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
        <div v-if="hiddenThreadCount > 0" class="thread-panel-footnote">
          还有 {{ hiddenThreadCount }} 条线程没有在这里展开，左侧“最近主题”列表支持继续浏览和右键操作。
        </div>
        <NEmpty v-else description="还没有主题线程" />
      </NCard>
    </section>

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
.dashboard-grid {
  display: grid;
  gap: 18px;
}

.hero-grid {
  grid-template-columns: 1.35fr 0.92fr;
  align-items: stretch;
}

.dashboard-grid {
  grid-template-columns: 0.9fr 1.1fr;
  align-items: start;
}

.hero-copy,
.hero-side {
  padding: 24px;
}

.hero-copy {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(163, 177, 138, 0.22), transparent 34%),
    linear-gradient(135deg, rgba(45, 106, 79, 0.09), rgba(255, 255, 255, 0.96) 48%, rgba(248, 246, 239, 0.94));
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 12px;
  color: #6a776c;
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

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.hero-flow {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.flow-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(45, 106, 79, 0.08);
}

.flow-step,
.principle-step {
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7d897f;
}

.flow-title,
.principle-title {
  margin-top: 8px;
  font-weight: 700;
  color: #233026;
}

.flow-copy,
.principle-copy,
.thread-panel-copy,
.guide-note,
.snapshot-note {
  margin-top: 8px;
  color: #526055;
  line-height: 1.65;
}

.hero-side-stack {
  display: grid;
  gap: 18px;
}

.hero-side-title {
  font-weight: 700;
}

.support-grid,
.snapshot-grid,
.principle-grid,
.thread-grid {
  display: grid;
  gap: 14px;
}

.support-grid {
  margin-top: 12px;
}

.support-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 16px;
}

.snapshot-grid,
.principle-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 12px;
}

.snapshot-item,
.principle-card {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.56);
  border: 1px solid rgba(45, 106, 79, 0.08);
}

.snapshot-label {
  color: #738176;
  font-size: 12px;
}

.snapshot-value {
  margin-top: 10px;
  font-size: 30px;
  font-weight: 700;
  color: #203025;
}

.snapshot-emerald {
  background: linear-gradient(135deg, rgba(45, 106, 79, 0.14), rgba(255, 255, 255, 0.7));
}

.snapshot-amber {
  background: linear-gradient(135deg, rgba(196, 137, 29, 0.14), rgba(255, 255, 255, 0.7));
}

.snapshot-stone {
  background: linear-gradient(135deg, rgba(108, 117, 125, 0.12), rgba(255, 255, 255, 0.7));
}

.snapshot-olive {
  background: linear-gradient(135deg, rgba(163, 177, 138, 0.18), rgba(255, 255, 255, 0.72));
}

.guide-note {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(45, 106, 79, 0.08);
}

.thread-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.thread-panel-meta {
  color: #738176;
  font-size: 13px;
  white-space: nowrap;
}

.thread-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.thread-card {
  display: block;
  padding: 18px;
  border-radius: 20px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.58)),
    linear-gradient(135deg, rgba(45, 106, 79, 0.06), transparent 60%);
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}

.thread-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 30px rgba(45, 106, 79, 0.08);
  border-color: rgba(45, 106, 79, 0.16);
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
  color: #223126;
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

.thread-panel-footnote {
  margin-top: 16px;
  color: #667469;
  line-height: 1.6;
}

@media (max-width: 1100px) {
  .hero-grid,
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .thread-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .hero-flow,
  .snapshot-grid,
  .principle-grid {
    grid-template-columns: 1fr;
  }

  .thread-panel-head {
    flex-direction: column;
  }
}
</style>
