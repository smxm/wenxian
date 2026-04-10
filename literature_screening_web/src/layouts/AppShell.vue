<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, reactive, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { ChevronDown, ChevronUp, Files, LayoutDashboard, Sparkles } from 'lucide-vue-next'
import { NBadge, NButton, NDropdown, NForm, NFormItem, NInput, NLayout, NLayoutContent, NLayoutSider, NMenu, NModal, NSpace, NText, useMessage } from 'naive-ui'
import { useDraftsStore } from '@/stores/drafts'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const tasksStore = useTasksStore()
const draftsStore = useDraftsStore()
const projectsStore = useProjectsStore()
const expandAllThreads = ref(false)
const editingProjectId = ref<string | null>(null)
const editForm = reactive({
  name: '',
  topic: '',
  description: ''
})
const threadContextMenu = ref<{
  show: boolean
  x: number
  y: number
  project: { id: string; name: string; topic: string; description: string } | null
}>({
  show: false,
  x: 0,
  y: 0,
  project: null
})

const menuOptions = [
  {
    key: '/',
    label: () => h(RouterLink, { to: '/' }, { default: () => '主题线程' }),
    icon: () => h(LayoutDashboard, { size: 18 })
  },
  {
    key: '/threads/new',
    label: () => h(RouterLink, { to: '/threads/new' }, { default: () => '新建线程' }),
    icon: () => h(Sparkles, { size: 18 })
  },
  {
    key: '/tasks',
    label: () => h(RouterLink, { to: '/tasks' }, { default: () => '后台任务' }),
    icon: () => h(Files, { size: 18 })
  }
]

const activeKey = computed(() => {
  if (route.path.startsWith('/tasks')) return '/tasks'
  if (route.path.startsWith('/threads/new') || route.path.startsWith('/strategy')) return '/threads/new'
  return '/'
})
const activeThreadId = computed(() => String(route.params.projectId ?? ''))
const screeningDraftRoute = computed(() =>
  draftsStore.screeningDraft.projectId ? `/threads/${draftsStore.screeningDraft.projectId}/screening/new` : '/screening/new'
)

const allRecentThreads = computed(() =>
  [...projectsStore.list].sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime())
)

const threadActionOptions = [
  { label: '打开线程', key: 'open' },
  { label: '编辑主题', key: 'edit' },
  { type: 'divider', key: 'divider' },
  { label: '删除线程', key: 'delete' }
]

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
  if (activeThreadId.value === project.id) {
    await router.push('/')
  }
  message.success('主题线程已删除')
}

function openThreadContextMenu(
  event: MouseEvent,
  project: { id: string; name: string; topic: string; description: string }
) {
  event.preventDefault()
  threadContextMenu.value = {
    show: true,
    x: event.clientX,
    y: event.clientY,
    project
  }
}

function closeThreadContextMenu() {
  threadContextMenu.value.show = false
  threadContextMenu.value.project = null
}

async function handleThreadMenuSelect(action: string) {
  const project = threadContextMenu.value.project
  closeThreadContextMenu()
  if (!project) return
  if (action === 'open') {
    await router.push(`/threads/${project.id}`)
    return
  }
  if (action === 'edit') {
    openEditThread(project)
    return
  }
  if (action === 'delete') {
    await removeThread(project)
  }
}

onMounted(() => {
  draftsStore.hydrate()
  void Promise.all([tasksStore.refreshList(), projectsStore.refreshProjects()])
  tasksStore.startPolling()
})

onUnmounted(() => {
  tasksStore.stopPolling()
})
</script>

<template>
  <NLayout has-sider class="app-shell">
    <NLayoutSider bordered collapse-mode="width" :collapsed-width="88" :width="320" class="shell-sider">
      <div class="sider-scroll">
        <div class="brand-block panel-surface">
          <div class="brand-row">
            <div class="brand-icon">
              <Sparkles :size="20" />
            </div>
            <div>
              <div class="brand-kicker">Thread-first Studio</div>
              <div class="brand-title">主题线程工作台</div>
            </div>
          </div>
          <p class="brand-copy">每个研究主题是一条线程。在线程里持续推进初筛、全文复核和报告生成。</p>
        </div>

        <NMenu :value="activeKey" :options="menuOptions" class="nav-menu" />

        <div class="thread-block panel-surface">
          <div class="section-header">
            <div>
              <div class="status-title">最近主题</div>
              <div class="section-subhint">左键进入线程，右键打开操作菜单</div>
            </div>
            <NButton
              v-if="allRecentThreads.length > 5"
              quaternary
              size="small"
              class="toggle-button"
              @click="expandAllThreads = !expandAllThreads"
            >
              <template #icon>
                <component :is="expandAllThreads ? ChevronUp : ChevronDown" :size="14" />
              </template>
              {{ expandAllThreads ? '收起' : '展开全部' }}
            </NButton>
          </div>

          <div
            v-if="allRecentThreads.length"
            class="thread-list"
            :class="{ expanded: expandAllThreads }"
          >
            <RouterLink
              v-for="project in allRecentThreads"
              :key="project.id"
              :to="`/threads/${project.id}`"
              class="thread-item"
              :class="{ active: activeThreadId === project.id }"
              @contextmenu.prevent="openThreadContextMenu($event, project)"
            >
              <div class="thread-item-title">{{ project.name }}</div>
              <div class="thread-item-copy">{{ project.topic }}</div>
            </RouterLink>
          </div>
          <div v-else class="empty-copy">还没有主题线程。先输入研究需求生成线程方案，再在线程里发起第一轮初筛。</div>
        </div>

        <div class="status-block panel-surface">
          <div class="status-title">运行状态</div>
          <NSpace vertical :size="10">
            <div class="status-row">
              <NText depth="3">运行中任务</NText>
              <NBadge :value="tasksStore.runningTasks.length" color="#2d6a4f" />
            </div>
            <div class="status-row">
              <NText depth="3">已完成报告</NText>
              <NBadge :value="tasksStore.completedReports.length" color="#8f5b1f" />
            </div>
            <div class="status-row">
              <NText depth="3">未提交草稿</NText>
              <NBadge :value="draftsStore.hasScreeningDraft ? 1 : 0" color="#6a776c" />
            </div>
            <NButton tertiary block @click="tasksStore.refreshList()">刷新任务</NButton>
            <RouterLink v-if="draftsStore.hasScreeningDraft" :to="screeningDraftRoute" class="status-link">
              继续编辑未提交的初筛草稿
            </RouterLink>
          </NSpace>

          <div v-if="tasksStore.runningTasks.length" class="running-list">
            <div class="running-title">正在执行</div>
            <RouterLink
              v-for="task in tasksStore.runningTasks.slice(0, 4)"
              :key="task.id"
              :to="`/tasks/${task.id}`"
              class="running-item"
            >
              <div class="running-item-title">{{ task.title }}</div>
              <div class="running-item-meta">
                {{ task.phase_label || task.phase }}
                <span v-if="task.progress_total"> · {{ task.progress_current || 0 }}/{{ task.progress_total }}</span>
              </div>
            </RouterLink>
          </div>
        </div>
      </div>
    </NLayoutSider>

    <NLayoutContent embedded content-style="padding: 28px;">
      <div class="topbar panel-surface">
        <div>
          <div class="topbar-eyebrow">Thread-first Studio</div>
          <div class="topbar-title">围绕主题连续推进初筛、全文复核与报告</div>
        </div>
        <div class="topbar-note">
          先用自然语言创建线程方案，再按“初筛 -> 全文 -> 报告”的顺序推进；线程顶部会一直固定当前主题和筛选标准。
        </div>
      </div>

      <RouterView />
    </NLayoutContent>
  </NLayout>

  <NDropdown
    trigger="manual"
    placement="bottom-start"
    :show="threadContextMenu.show"
    :x="threadContextMenu.x"
    :y="threadContextMenu.y"
    :options="threadActionOptions"
    @clickoutside="closeThreadContextMenu"
    @select="handleThreadMenuSelect"
  />

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
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.shell-sider {
  background: transparent;
}

.sider-scroll {
  height: 100vh;
  overflow-y: auto;
  padding: 22px 16px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  scrollbar-width: thin;
}

.brand-block,
.thread-block,
.status-block,
.topbar {
  padding: 20px;
}

.brand-row {
  display: flex;
  gap: 14px;
  align-items: center;
}

.brand-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: linear-gradient(135deg, #2d6a4f 0%, #a3b18a 100%);
  color: white;
}

.brand-kicker,
.topbar-eyebrow {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #6d7d70;
}

.brand-title,
.topbar-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2520;
}

.brand-copy,
.topbar-note {
  margin: 12px 0 0;
  color: #5b665d;
  line-height: 1.6;
}

.nav-menu {
  border-radius: 24px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-subhint {
  margin-top: 4px;
  font-size: 12px;
  color: #7b857d;
}

.status-title,
.running-title {
  font-weight: 700;
}

.toggle-button {
  flex-shrink: 0;
}

.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-link {
  color: #2d6a4f;
  font-size: 13px;
}

.thread-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 420px;
  overflow-y: auto;
  padding-right: 6px;
  scrollbar-width: thin;
}

.thread-list.expanded {
  max-height: none;
  overflow: visible;
  padding-right: 0;
}

.thread-item,
.running-item {
  display: block;
}

.thread-item {
  padding: 14px 12px;
  margin: 0 2px;
  border-radius: 18px;
  transition: background 160ms ease, transform 160ms ease, box-shadow 160ms ease;
}

.thread-item:hover {
  background: rgba(45, 106, 79, 0.07);
  transform: translateY(-1px);
}

.thread-item.active {
  background: linear-gradient(135deg, rgba(45, 106, 79, 0.12), rgba(163, 177, 138, 0.18));
  box-shadow: inset 0 0 0 1px rgba(45, 106, 79, 0.16);
}

.thread-item + .thread-item,
.running-item + .running-item {
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.thread-item-title,
.running-item-title {
  font-weight: 600;
  color: #1f2520;
  line-height: 1.45;
}

.thread-item-copy,
.running-item-meta {
  margin-top: 6px;
  color: #5b665d;
  font-size: 13px;
  line-height: 1.6;
}

.empty-copy {
  color: #5b665d;
  line-height: 1.7;
}

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
}

.running-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.running-item {
  padding-top: 10px;
}

@media (max-width: 1024px) {
  .topbar {
    flex-direction: column;
  }

  .sider-scroll {
    height: auto;
    max-height: 60vh;
  }

  .thread-list {
    max-height: 260px;
  }
}
</style>
