<script setup lang="ts">
import { computed, h, onMounted, onUnmounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { FileSearch, Files, LayoutDashboard, Sparkles } from 'lucide-vue-next'
import { NBadge, NButton, NLayout, NLayoutContent, NLayoutSider, NMenu, NSpace, NText } from 'naive-ui'
import { useDraftsStore } from '@/stores/drafts'
import { useTasksStore } from '@/stores/tasks'

const route = useRoute()
const tasksStore = useTasksStore()
const draftsStore = useDraftsStore()

const menuOptions = [
  {
    key: '/',
    label: () => h(RouterLink, { to: '/' }, { default: () => '总览' }),
    icon: () => h(LayoutDashboard, { size: 18 })
  },
  {
    key: '/screening/new',
    label: () => h(RouterLink, { to: '/screening/new' }, { default: () => '新建初筛' }),
    icon: () => h(FileSearch, { size: 18 })
  },
  {
    key: '/tasks',
    label: () => h(RouterLink, { to: '/tasks' }, { default: () => '任务中心' }),
    icon: () => h(Files, { size: 18 })
  }
]

const activeKey = computed(() => {
  if (route.path.startsWith('/tasks')) return '/tasks'
  if (route.path.startsWith('/screening')) return '/screening/new'
  return '/'
})

onMounted(() => {
  draftsStore.hydrate()
  void tasksStore.refreshList()
  tasksStore.startPolling()
})

onUnmounted(() => {
  tasksStore.stopPolling()
})
</script>

<template>
  <NLayout has-sider class="app-shell">
    <NLayoutSider
      bordered
      collapse-mode="width"
      :collapsed-width="88"
      :width="292"
      content-style="padding: 22px 16px;"
      class="shell-sider"
    >
      <div class="brand-block panel-surface">
        <div class="brand-row">
          <div class="brand-icon">
            <Sparkles :size="20" />
          </div>
          <div>
            <div class="brand-kicker">Literature Workbench</div>
            <div class="brand-title">文献筛选工作台</div>
          </div>
        </div>
        <p class="brand-copy">把初筛、任务管理和简洁报告放进同一个本地工作流。</p>
      </div>

      <NMenu :value="activeKey" :options="menuOptions" class="nav-menu" />

      <div class="status-block panel-surface">
        <div class="status-title">状态概览</div>
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
          <div class="running-title">正在运行</div>
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
    </NLayoutSider>

    <NLayoutContent embedded content-style="padding: 28px;">
      <div class="topbar panel-surface">
        <div>
          <div class="topbar-eyebrow">Studio</div>
          <div class="topbar-title">把初筛与整理报告放进同一个现代工作台</div>
        </div>
        <div class="topbar-note">主流程负责初筛，简洁报告作为下游任务独立生成，前端统一走稳定 API。</div>
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

.brand-block,
.status-block,
.topbar {
  padding: 18px;
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
  margin: 18px 0;
  border-radius: 24px;
  overflow: hidden;
}

.status-title,
.running-title {
  font-weight: 700;
  margin-bottom: 10px;
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

.running-list {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.running-item {
  display: block;
  padding: 10px 0;
}

.running-item + .running-item {
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.running-item-title {
  font-weight: 600;
  color: #1f2520;
}

.running-item-meta {
  margin-top: 4px;
  color: #5b665d;
  font-size: 13px;
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
}
</style>
