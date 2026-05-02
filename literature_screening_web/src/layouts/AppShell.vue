<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, reactive, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { ChevronDown, ChevronUp, Files, LayoutDashboard, Sparkles } from 'lucide-vue-next'
import { NButton, NDropdown, NForm, NFormItem, NInput, NLayout, NLayoutContent, NLayoutSider, NMenu, NModal, NSpace, useMessage } from 'naive-ui'
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
  if (!window.confirm(`确认删除主题“${project.name}”？相关初筛和报告生成任务也会一起删除。`)) {
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
              <div class="brand-kicker">Literature Review Studio</div>
              <div class="brand-title">文献综研工作台</div>
            </div>
          </div>
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
      </div>
    </NLayoutSider>

    <NLayoutContent embedded content-style="padding: 28px;">
      <div class="topbar panel-surface">
        <div>
          <div class="topbar-eyebrow">Literature Review Studio</div>
          <div class="topbar-title">围绕主题管理初筛、复核、全文获取与报告生成</div>
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
  height: 100dvh;
  min-height: 0;
  overflow-y: auto;
  padding: 22px 16px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  scrollbar-width: thin;
}

.brand-block,
.thread-block,
.topbar {
  padding: 20px;
}

.brand-block,
.nav-menu {
  flex: 0 0 auto;
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

.nav-menu {
  border-radius: 24px;
  overflow: hidden;
}

.nav-menu :deep(.n-menu-item-content) {
  min-height: 56px;
}

.thread-block {
  display: flex;
  min-height: 0;
  flex: 0 0 auto;
  flex-direction: column;
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

.status-title {
  font-weight: 700;
}

.toggle-button {
  flex-shrink: 0;
}

.thread-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 52vh;
  min-height: 0;
  overflow-y: auto;
  padding-right: 6px;
  scrollbar-width: thin;
}

.thread-list.expanded {
  max-height: none;
  overflow-y: visible;
  padding-right: 0;
}

.thread-item {
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

.thread-item + .thread-item {
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.thread-item-title {
  font-weight: 600;
  color: #1f2520;
  line-height: 1.45;
}

.thread-item-copy {
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

@media (max-width: 1024px) {
  .topbar {
    flex-direction: column;
  }

  .sider-scroll {
    height: 100vh;
    height: 100dvh;
    max-height: none;
  }

  .thread-list {
    max-height: 52vh;
  }
}
</style>
