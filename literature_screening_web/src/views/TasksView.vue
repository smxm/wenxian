<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import dayjs from 'dayjs'
import { NButton, NCard, NEmpty, NGrid, NGridItem, NInput, NProgress, NSelect, NText } from 'naive-ui'
import StatusPill from '@/components/StatusPill.vue'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'

const tasksStore = useTasksStore()
const projectsStore = useProjectsStore()

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const kindFilter = ref<string | null>(null)
const projectFilter = ref<string | null>(null)

const projectOptions = computed(() =>
  projectsStore.list.map((project) => ({
    label: project.name,
    value: project.id
  }))
)

const filteredTasks = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return tasksStore.list.filter((task) => {
    if (statusFilter.value && task.status !== statusFilter.value) return false
    if (kindFilter.value && task.kind !== kindFilter.value) return false
    if (projectFilter.value && task.project_id !== projectFilter.value) return false
    if (!query) return true
    return [task.title, task.phase, task.project_topic ?? '', task.project_id ?? '']
      .some((value) => value.toLowerCase().includes(query))
  })
})

function progressOf(task: { progress_current?: number | null; progress_total?: number | null }) {
  if (!task.progress_total || task.progress_total <= 0 || task.progress_current === null || task.progress_current === undefined) {
    return null
  }
  return Math.max(0, Math.min(100, Math.round((task.progress_current / task.progress_total) * 100)))
}

onMounted(async () => {
  await Promise.all([tasksStore.refreshList(), projectsStore.refreshProjects()])
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

    <NCard class="panel-surface">
      <div class="filters">
        <NInput v-model:value="keyword" placeholder="搜索任务标题、项目或主题" clearable />
        <NSelect
          v-model:value="projectFilter"
          clearable
          :options="projectOptions"
          placeholder="项目"
        />
        <NSelect
          v-model:value="kindFilter"
          clearable
          :options="[
            { label: '初筛任务', value: 'screening' },
            { label: '报告任务', value: 'report' }
          ]"
          placeholder="任务类型"
        />
        <NSelect
          v-model:value="statusFilter"
          clearable
          :options="[
            { label: '待运行', value: 'pending' },
            { label: '运行中', value: 'running' },
            { label: '成功', value: 'succeeded' },
            { label: '失败', value: 'failed' }
          ]"
          placeholder="状态"
        />
      </div>
    </NCard>

    <NEmpty v-if="!filteredTasks.length" description="当前筛选条件下没有任务。" class="panel-surface empty-state" />

    <NGrid v-else :cols="2" :x-gap="18" :y-gap="18" responsive="screen" item-responsive>
      <NGridItem v-for="task in filteredTasks" :key="task.id" span="2 m:1">
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
              <div><NText depth="3">项目</NText> {{ task.project_id || '-' }}</div>
              <div><NText depth="3">主题</NText> {{ task.project_topic || '-' }}</div>
              <div><NText depth="3">尝试</NText> {{ task.attempt_count }}</div>
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

.filters {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 12px;
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

@media (max-width: 1100px) {
  .filters {
    grid-template-columns: 1fr;
  }
}
</style>
