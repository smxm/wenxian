<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import dayjs from 'dayjs'
import { NButton, NCard, NEmpty, NInput, NProgress, NSelect, NTag, NText } from 'naive-ui'
import StatusPill from '@/components/StatusPill.vue'
import { useDraftsStore } from '@/stores/drafts'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import type { TaskSnapshot } from '@/types/api'

const tasksStore = useTasksStore()
const projectsStore = useProjectsStore()
const draftsStore = useDraftsStore()

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const kindFilter = ref<string | null>(null)
const projectFilter = ref<string | null>(null)

const projectMap = computed(() => new Map(projectsStore.list.map((project) => [project.id, project])))

const projectOptions = computed(() =>
  projectsStore.list.map((project) => ({
    label: project.name,
    value: project.id
  }))
)

const sortedTasks = computed(() =>
  [...tasksStore.list].sort((left, right) => dayjs(right.updated_at).valueOf() - dayjs(left.updated_at).valueOf())
)

const filteredTasks = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return sortedTasks.value.filter((task) => {
    if (statusFilter.value && task.status !== statusFilter.value) return false
    if (kindFilter.value && task.kind !== kindFilter.value) return false
    if (projectFilter.value && task.project_id !== projectFilter.value) return false
    if (!query) return true
    const project = task.project_id ? projectMap.value.get(task.project_id) : null
    return [
      task.title,
      task.phase,
      task.phase_label ?? '',
      task.project_topic ?? '',
      task.project_id ?? '',
      project?.name ?? '',
      project?.topic ?? ''
    ].some((value) => value.toLowerCase().includes(query))
  })
})

const groupedTasks = computed(() => {
  const groups = new Map<string, { projectId: string | null; title: string; topic: string; tasks: TaskSnapshot[] }>()
  for (const task of filteredTasks.value) {
    const projectId = task.project_id ?? null
    const groupKey = projectId ?? 'unassigned'
    if (!groups.has(groupKey)) {
      const project = projectId ? projectMap.value.get(projectId) : null
      groups.set(groupKey, {
        projectId,
        title: project?.name ?? '未关联线程',
        topic: project?.topic ?? task.project_topic ?? '没有关联主题',
        tasks: []
      })
    }
    groups.get(groupKey)?.tasks.push(task)
  }
  return Array.from(groups.values()).sort((left, right) => {
    const leftRunning = left.tasks.some((task) => task.status === 'running')
    const rightRunning = right.tasks.some((task) => task.status === 'running')
    if (leftRunning !== rightRunning) return leftRunning ? -1 : 1
    const leftUpdated = Math.max(...left.tasks.map((task) => dayjs(task.updated_at).valueOf()))
    const rightUpdated = Math.max(...right.tasks.map((task) => dayjs(task.updated_at).valueOf()))
    return rightUpdated - leftUpdated
  })
})

const runningTasks = computed(() => sortedTasks.value.filter((task) => task.status === 'running'))
const pendingTasks = computed(() => sortedTasks.value.filter((task) => task.status === 'pending'))
const failedTasks = computed(() => sortedTasks.value.filter((task) => task.status === 'failed'))
const succeededTasks = computed(() => sortedTasks.value.filter((task) => task.status === 'succeeded'))
const screeningDraftRoute = computed(() =>
  draftsStore.screeningDraft.projectId ? `/threads/${draftsStore.screeningDraft.projectId}/screening/new` : '/screening/new'
)

function progressOf(task: { progress_current?: number | null; progress_total?: number | null }) {
  if (!task.progress_total || task.progress_total <= 0 || task.progress_current === null || task.progress_current === undefined) {
    return null
  }
  return Math.max(0, Math.min(100, Math.round((task.progress_current / task.progress_total) * 100)))
}

function taskKindLabel(task: TaskSnapshot) {
  if (task.kind === 'screening') return '初筛任务'
  if (task.kind === 'report') return '报告生成'
  if (task.kind === 'strategy') return '策略任务'
  return '任务'
}

function taskKindType(task: TaskSnapshot) {
  if (task.kind === 'screening') return 'success'
  if (task.kind === 'report') return 'warning'
  return 'default'
}

function projectName(task: TaskSnapshot) {
  return task.project_id ? projectMap.value.get(task.project_id)?.name ?? task.project_id : '未关联线程'
}

function selectRunningTasks() {
  statusFilter.value = 'running'
}

onMounted(async () => {
  draftsStore.hydrate()
  await Promise.all([tasksStore.refreshList(), projectsStore.refreshProjects()])
})
</script>

<template>
  <div class="tasks-view">
    <div class="header-row">
      <div>
        <div class="eyebrow">Task Center</div>
        <h1>后台任务</h1>
      </div>
      <NButton tertiary @click="tasksStore.refreshList()">刷新</NButton>
    </div>

    <section class="status-overview">
      <button class="status-card running" type="button" @click="selectRunningTasks">
        <span>运行中</span>
        <strong>{{ runningTasks.length }}</strong>
      </button>
      <button class="status-card" type="button" @click="statusFilter = 'pending'">
        <span>待运行</span>
        <strong>{{ pendingTasks.length }}</strong>
      </button>
      <button class="status-card danger" type="button" @click="statusFilter = 'failed'">
        <span>失败</span>
        <strong>{{ failedTasks.length }}</strong>
      </button>
      <button class="status-card done" type="button" @click="kindFilter = null; statusFilter = 'succeeded'">
        <span>已完成任务</span>
        <strong>{{ succeededTasks.length }}</strong>
      </button>
      <RouterLink class="status-card draft" :to="screeningDraftRoute">
        <span>未提交草稿</span>
        <strong>{{ draftsStore.hasScreeningDraft ? 1 : 0 }}</strong>
      </RouterLink>
    </section>

    <NCard v-if="runningTasks.length" class="panel-surface running-panel" embedded>
      <div class="section-head">
        <div>
          <div class="section-title">正在运行</div>
          <div class="section-copy">当前任务会优先显示在这里，可以直接进入查看日志和进度。</div>
        </div>
        <NTag round type="success">{{ runningTasks.length }} 个任务</NTag>
      </div>
      <div class="running-task-list">
        <RouterLink v-for="task in runningTasks" :key="task.id" :to="`/tasks/${task.id}`" class="running-task-card">
          <div class="running-task-head">
            <div>
              <div class="task-thread">{{ projectName(task) }}</div>
              <div class="running-task-title">{{ task.title }}</div>
            </div>
            <StatusPill :status="task.status" />
          </div>
          <div class="running-task-meta">
            {{ task.phase_label || task.phase }}
            <span v-if="task.progress_total"> · {{ task.progress_current || 0 }}/{{ task.progress_total }}</span>
          </div>
          <NProgress
            v-if="progressOf(task) !== null"
            class="task-progress"
            type="line"
            :percentage="progressOf(task) || 0"
            :indicator-placement="'inside'"
          />
          <div v-else-if="task.progress_message" class="task-progress-copy">{{ task.progress_message }}</div>
        </RouterLink>
      </div>
    </NCard>

    <NCard class="panel-surface" embedded>
      <div class="filters">
        <NInput v-model:value="keyword" placeholder="搜索任务标题、线程或主题" clearable />
        <NSelect
          v-model:value="projectFilter"
          clearable
          :options="projectOptions"
          placeholder="线程"
        />
        <NSelect
          v-model:value="kindFilter"
          clearable
          :options="[
            { label: '策略任务', value: 'strategy' },
            { label: '初筛任务', value: 'screening' },
            { label: '报告生成', value: 'report' }
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
            { label: '失败', value: 'failed' },
            { label: '已取消', value: 'cancelled' }
          ]"
          placeholder="状态"
        />
      </div>
    </NCard>

    <NEmpty v-if="!filteredTasks.length" description="当前筛选条件下没有任务。" class="panel-surface empty-state" />

    <section v-else class="thread-task-groups">
      <NCard v-for="group in groupedTasks" :key="group.projectId ?? 'unassigned'" class="panel-surface thread-task-group" embedded>
        <div class="group-head">
          <div>
            <div class="group-title">{{ group.title }}</div>
            <div class="group-topic">{{ group.topic }}</div>
          </div>
          <div class="group-tags">
            <NTag round>{{ group.tasks.length }} 个任务</NTag>
            <NTag v-if="group.tasks.some((task) => task.status === 'running')" round type="success">运行中</NTag>
          </div>
        </div>

        <div class="task-list">
          <RouterLink v-for="task in group.tasks" :key="task.id" :to="`/tasks/${task.id}`" class="task-card" :class="[`kind-${task.kind}`, `status-${task.status}`]">
            <div class="task-header">
              <div>
                <div class="task-labels">
                  <NTag round size="small" :type="taskKindType(task)">{{ taskKindLabel(task) }}</NTag>
                  <NTag round size="small">{{ dayjs(task.updated_at).format('MM-DD HH:mm') }}</NTag>
                </div>
                <div class="task-title">{{ task.title }}</div>
              </div>
              <StatusPill :status="task.status" />
            </div>

            <div class="task-meta">
              <div><NText depth="3">阶段</NText> {{ task.phase_label || task.phase }}</div>
              <div><NText depth="3">模型</NText> {{ task.model_provider || '-' }}</div>
              <div><NText depth="3">主题</NText> {{ task.project_topic || group.topic || '-' }}</div>
              <div><NText depth="3">尝试</NText> {{ task.attempt_count }}</div>
            </div>

            <NProgress
              v-if="progressOf(task) !== null"
              class="task-progress"
              type="line"
              :percentage="progressOf(task) || 0"
              :indicator-placement="'inside'"
            />
            <div v-else-if="task.progress_message" class="task-progress-copy">{{ task.progress_message }}</div>
          </RouterLink>
        </div>
      </NCard>
    </section>
  </div>
</template>

<style scoped>
.tasks-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.header-row,
.section-head,
.group-head,
.task-header,
.running-task-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.header-row {
  align-items: flex-end;
}

.section-head,
.group-head,
.task-header,
.running-task-head {
  align-items: flex-start;
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

.status-overview {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.status-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  padding: 16px 18px;
  border: 1px solid rgba(191, 181, 165, 0.45);
  border-radius: 18px;
  background: rgba(255, 253, 248, 0.9);
  color: #1f2520;
  text-align: left;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(41, 50, 45, 0.06);
}

.status-card span {
  color: #5b665d;
}

.status-card strong {
  font-size: 30px;
  line-height: 1;
}

.status-card.running {
  background: linear-gradient(135deg, rgba(45, 106, 79, 0.14), rgba(163, 177, 138, 0.18));
  border-color: rgba(45, 106, 79, 0.18);
}

.status-card.danger {
  background: rgba(255, 247, 242, 0.94);
}

.status-card.done {
  background: rgba(252, 248, 237, 0.94);
}

.status-card.draft {
  text-decoration: none;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
}

.section-copy,
.group-topic,
.task-thread,
.running-task-meta,
.task-progress-copy {
  color: #5b665d;
  line-height: 1.6;
}

.running-panel {
  border-color: rgba(45, 106, 79, 0.2);
}

.running-task-list,
.thread-task-groups,
.task-list {
  display: flex;
  flex-direction: column;
}

.running-task-list {
  gap: 12px;
  margin-top: 16px;
}

.running-task-card,
.task-card {
  display: block;
  border-radius: 16px;
  color: inherit;
}

.running-task-card {
  padding: 16px;
  border: 1px solid rgba(45, 106, 79, 0.16);
  background: rgba(247, 252, 248, 0.9);
}

.running-task-title,
.task-title,
.group-title {
  font-weight: 700;
  color: #1f2520;
}

.running-task-title {
  margin-top: 4px;
  font-size: 18px;
}

.filters {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 12px;
}

.thread-task-groups {
  gap: 16px;
}

.thread-task-group {
  border-radius: 20px;
}

.group-tags,
.task-labels {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.task-list {
  gap: 12px;
  margin-top: 16px;
}

.task-card {
  padding: 16px;
  border: 1px solid rgba(191, 181, 165, 0.36);
  background: rgba(255, 255, 255, 0.78);
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.task-card:hover {
  transform: translateY(-1px);
  border-color: rgba(45, 106, 79, 0.22);
  box-shadow: 0 12px 28px rgba(41, 50, 45, 0.08);
}

.task-card.status-running {
  border-left: 6px solid #2d6a4f;
  background: rgba(247, 252, 248, 0.92);
}

.task-card.status-failed {
  border-left: 6px solid #b54f25;
}

.task-card.kind-report {
  box-shadow: inset 4px 0 0 rgba(143, 91, 31, 0.22);
}

.task-card.kind-screening {
  box-shadow: inset 4px 0 0 rgba(45, 106, 79, 0.18);
}

.task-title {
  margin-top: 10px;
  font-size: 18px;
  line-height: 1.35;
}

.task-meta {
  margin-top: 14px;
  display: grid;
  gap: 8px;
  color: #4e5a51;
}

.task-progress {
  margin-top: 14px;
}

.task-progress-copy {
  margin-top: 14px;
}

.empty-state {
  padding: 30px;
}

@media (max-width: 1100px) {
  .filters,
  .status-overview {
    grid-template-columns: 1fr;
  }

  .header-row,
  .section-head,
  .group-head,
  .task-header,
  .running-task-head {
    flex-direction: column;
  }

  .group-tags,
  .task-labels {
    justify-content: flex-start;
  }
}
</style>
