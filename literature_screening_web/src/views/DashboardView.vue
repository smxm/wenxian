<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { ArrowRight, Bot, FolderOpenDot, LayoutPanelTop } from 'lucide-vue-next'
import { NButton, NCard, NEmpty, NList, NListItem, NSpace, NText } from 'naive-ui'
import OverviewMetric from '@/components/OverviewMetric.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useDraftsStore } from '@/stores/drafts'
import { useMetaStore } from '@/stores/meta'
import { useTasksStore } from '@/stores/tasks'

const metaStore = useMetaStore()
const tasksStore = useTasksStore()
const draftsStore = useDraftsStore()

const stats = computed(() => {
  const tasks = tasksStore.list
  return {
    total: tasks.length,
    running: tasks.filter((task) => task.status === 'running' || task.status === 'pending').length,
    screening: tasks.filter((task) => task.kind === 'screening').length,
    reports: tasks.filter((task) => task.kind === 'report').length
  }
})

onMounted(async () => {
  draftsStore.hydrate()
  await Promise.all([metaStore.ensureLoaded(), tasksStore.refreshList()])
})
</script>

<template>
  <div class="view-stack">
    <section class="hero-grid">
      <div class="hero-copy panel-surface">
        <div class="eyebrow">Workbench Overview</div>
        <h1>把文献输入、初筛执行、结果复查和简洁报告放进同一套前端工作流</h1>
        <p>前端只依赖稳定 API，不直接绑定底层 Python 文件结构。筛选模块和报告模块可以继续演进，界面不会跟着一起失控。</p>
        <NSpace>
          <RouterLink to="/screening/new">
            <NButton type="primary" size="large">
              {{ draftsStore.hasScreeningDraft ? '继续编辑初筛草稿' : '新建初筛' }}
              <template #icon>
                <ArrowRight :size="16" />
              </template>
            </NButton>
          </RouterLink>
          <RouterLink to="/tasks">
            <NButton tertiary size="large">查看任务中心</NButton>
          </RouterLink>
        </NSpace>
      </div>

      <div class="hero-side panel-surface">
        <div class="hero-side-title">当前支持</div>
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
            <LayoutPanelTop :size="18" />
            <span>草稿自动保存，任务统一轮询，报告独立生成</span>
          </div>
        </div>
      </div>
    </section>

    <section class="metric-grid">
      <OverviewMetric label="总任务数" :value="stats.total" />
      <OverviewMetric label="运行中" :value="stats.running" />
      <OverviewMetric label="初筛任务" :value="stats.screening" />
      <OverviewMetric label="报告任务" :value="stats.reports" />
    </section>

    <section class="dashboard-grid">
      <NCard title="最近任务" class="panel-surface">
        <NList hoverable clickable v-if="tasksStore.list.length">
          <NListItem v-for="task in tasksStore.list.slice(0, 6)" :key="task.id">
            <RouterLink :to="`/tasks/${task.id}`" class="task-link">
              <div>
                <div class="task-title">{{ task.title }}</div>
                <NText depth="3">{{ task.kind === 'screening' ? '初筛任务' : '报告任务' }}</NText>
              </div>
              <StatusPill :status="task.status" />
            </RouterLink>
          </NListItem>
        </NList>
        <NEmpty v-else description="还没有任务记录。" />
      </NCard>

      <NCard title="当前工作方式" class="panel-surface">
        <ul class="principles">
          <li>初筛表单会自动保存为草稿，切换页面不会丢。</li>
          <li>任务中心持续显示所有运行中的任务，不再依赖单页停留。</li>
          <li>初筛成功后可直接创建简洁报告任务，并查看生成进度。</li>
          <li>后续新增模型、模板或任务类型，只扩展 API 和组件，不重写整套前端。</li>
        </ul>
      </NCard>
    </section>
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

.task-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.task-title {
  font-weight: 700;
}

.principles {
  margin: 0;
  padding-left: 18px;
  color: #4e5b51;
  line-height: 1.8;
}

@media (max-width: 1100px) {
  .hero-grid,
  .dashboard-grid,
  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
