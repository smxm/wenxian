<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { ChevronDown, ChevronUp, FileSearch, Files, LayoutDashboard, Sparkles } from 'lucide-vue-next'
import { NBadge, NButton, NLayout, NLayoutContent, NLayoutSider, NMenu, NSpace, NText } from 'naive-ui'
import { useDraftsStore } from '@/stores/drafts'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'

const route = useRoute()
const tasksStore = useTasksStore()
const draftsStore = useDraftsStore()
const projectsStore = useProjectsStore()
const expandAllThreads = ref(false)

const menuOptions = [
  {
    key: '/',
    label: () => h(RouterLink, { to: '/' }, { default: () => '主题线程' }),
    icon: () => h(LayoutDashboard, { size: 18 })
  },
  {
    key: '/screening/new',
    label: () => h(RouterLink, { to: '/screening/new' }, { default: () => '高级初筛' }),
    icon: () => h(FileSearch, { size: 18 })
  },
  {
    key: '/tasks',
    label: () => h(RouterLink, { to: '/tasks' }, { default: () => '后台任务' }),
    icon: () => h(Files, { size: 18 })
  }
]

const activeKey = computed(() => {
  if (route.path.startsWith('/tasks')) return '/tasks'
  if (route.path.startsWith('/screening')) return '/screening/new'
  return '/'
})

const allRecentThreads = computed(() => projectsStore.list)
const visibleRecentThreads = computed(() =>
  expandAllThreads.value ? allRecentThreads.value : allRecentThreads.value.slice(0, 5)
)

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
          <p class="brand-copy">每个研究主题是一条线程。在线程里持续推进初筛、人工复核和报告生成。</p>
        </div>

        <NMenu :value="activeKey" :options="menuOptions" class="nav-menu" />

        <div class="thread-block panel-surface">
          <div class="section-header">
            <div>
              <div class="status-title">最近主题</div>
              <div class="section-subtitle">默认显示 5 条，可滚动查看，也可展开全部。</div>
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
            v-if="visibleRecentThreads.length"
            class="thread-list"
            :class="{ expanded: expandAllThreads }"
          >
            <RouterLink
              v-for="project in visibleRecentThreads"
              :key="project.id"
              :to="`/threads/${project.id}`"
              class="thread-item"
            >
              <div class="thread-item-title">{{ project.name }}</div>
              <div class="thread-item-copy">{{ project.topic }}</div>
            </RouterLink>
          </div>
          <div v-else class="empty-copy">还没有主题线程。先新建一个主题，再在线程里发起第一轮初筛。</div>
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
            <RouterLink v-if="draftsStore.hasScreeningDraft" to="/screening/new" class="status-link">
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
          <div class="topbar-title">围绕主题连续推进初筛、复核与报告</div>
        </div>
        <div class="topbar-note">
          前端只暴露主题线程、本轮结果和下一步动作。底层任务、文件和数据注册继续保留在系统内部。
        </div>
      </div>

      <RouterView />
    </NLayoutContent>
  </NLayout>
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

.status-title,
.running-title {
  font-weight: 700;
}

.section-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #6b776d;
  line-height: 1.5;
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
  padding: 14px 0;
  margin: 0 2px;
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
