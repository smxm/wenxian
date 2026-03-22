<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import dayjs from 'dayjs'
import { NButton, NCard, NEmpty, NGrid, NGridItem, NProgress, NText } from 'naive-ui'
import StatusPill from '@/components/StatusPill.vue'
import { useTasksStore } from '@/stores/tasks'

const tasksStore = useTasksStore()

const sortedTasks = computed(() => tasksStore.list)

function progressOf(task: { progress_current?: number | null; progress_total?: number | null }) {
  if (!task.progress_total || task.progress_total <= 0 || task.progress_current === null || task.progress_current === undefined) {
    return null
  }
  return Math.max(0, Math.min(100, Math.round((task.progress_current / task.progress_total) * 100)))
}

onMounted(() => {
  void tasksStore.refreshList()
})
</script>

<template>
  <div class="tasks-view">
    <div class="header-row">
      <div>
        <div class="eyebrow">Task Center</div>
        <h1>任务中心</h1>
      </div>
      <NButton tertiary @click="tasksStore.refreshList()">刷新</NButton>
    </div>

    <NEmpty v-if="!sortedTasks.length" description="还没有任务。" class="panel-surface empty-state" />

    <NGrid v-else :cols="2" :x-gap="18" :y-gap="18" responsive="screen" item-responsive>
      <NGridItem v-for="task in sortedTasks" :key="task.id" span="2 m:1">
        <RouterLink :to="`/tasks/${task.id}`">
          <NCard class="panel-surface task-card" hoverable embedded>
            <div class="task-header">
              <div>
                <div class="task-kind">{{ task.kind === 'screening' ? '初筛任务' : '报告任务' }}</div>
                <div class="task-title">{{ task.title }}</div>
              </div>
              <StatusPill :status="task.status" />
            </div>

            <div class="task-meta">
              <div><NText depth="3">阶段</NText> {{ task.phase_label || task.phase }}</div>
              <div><NText depth="3">模型</NText> {{ task.model_provider || '-' }}</div>
              <div><NText depth="3">主题</NText> {{ task.project_topic || '-' }}</div>
              <div><NText depth="3">更新时间</NText> {{ dayjs(task.updated_at).format('YYYY-MM-DD HH:mm:ss') }}</div>
            </div>

            <NProgress
              v-if="progressOf(task) !== null"
              class="task-progress"
              type="line"
              :percentage="progressOf(task) || 0"
              :indicator-placement="'inside'"
            />
            <div v-else-if="task.progress_message" class="task-progress-copy">{{ task.progress_message }}</div>
          </NCard>
        </RouterLink>
      </NGridItem>
    </NGrid>
  </div>
</template>

<style scoped>
.tasks-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 12px;
  color: #6a776c;
}

h1 {
  margin: 6px 0 0;
}

.task-card {
  border-radius: 24px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.task-kind {
  color: #6a776c;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.task-title {
  margin-top: 8px;
  font-size: 20px;
  font-weight: 700;
}

.task-meta {
  margin-top: 18px;
  display: grid;
  gap: 8px;
  color: #4e5a51;
}

.task-progress {
  margin-top: 16px;
}

.task-progress-copy {
  margin-top: 16px;
  color: #5b665d;
}

.empty-state {
  padding: 30px;
}
</style>
