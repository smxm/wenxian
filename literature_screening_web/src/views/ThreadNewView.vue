<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { ArrowRight, FileSearch, Sparkles, Wand2 } from 'lucide-vue-next'
import { NButton, NCard, NForm, NFormItem, NInput, useMessage } from 'naive-ui'
import { useDraftsStore } from '@/stores/drafts'
import { useProjectsStore } from '@/stores/projects'
import type { ThreadProfile } from '@/types/api'

const router = useRouter()
const message = useMessage()
const draftsStore = useDraftsStore()
const projectsStore = useProjectsStore()

const newProjectName = ref('')
const newProjectDescription = ref('')
const researchNeed = ref('')
const draftNoticeDismissed = ref(false)
const creatingThread = ref(false)

function compactText(value: string) {
  return value.replace(/\s+/g, ' ').trim()
}

const compactResearchNeed = computed(() => compactText(researchNeed.value))
const fallbackThreadTitle = computed(() => compactResearchNeed.value.slice(0, 80))
const resolvedThreadName = computed(() => compactText(newProjectName.value) || fallbackThreadTitle.value || '新建线程')
const resolvedThreadDescription = computed(() => compactText(newProjectDescription.value) || compactResearchNeed.value)
const resolvedProjectTopic = computed(() => fallbackThreadTitle.value || resolvedThreadName.value)
const canCreateThread = computed(() => Boolean(compactResearchNeed.value))

function restoreDraft() {
  const draft = draftsStore.strategyDraft
  newProjectName.value = draft.newProjectName
  newProjectDescription.value = draft.newProjectDescription
  researchNeed.value = draft.researchNeed
  draftNoticeDismissed.value = true
}

function discardDraft() {
  draftsStore.clearStrategyDraft()
  draftNoticeDismissed.value = true
}

function persistDraft() {
  draftsStore.updateStrategyDraft({
    newProjectName: newProjectName.value,
    newProjectDescription: newProjectDescription.value,
    title: resolvedThreadName.value,
    projectTopic: resolvedProjectTopic.value,
    researchNeed: researchNeed.value
  })
}

function buildThreadProfile(base: ThreadProfile | null, threadUpdatedAt: string) {
  return {
    strategy: {
      ...(base?.strategy ?? {
        research_need: '',
        selected_databases: ['scopus', 'wos', 'pubmed', 'cnki'],
        model: null,
        latest_task_id: null,
        plan: null
      }),
      research_need: compactResearchNeed.value
    },
    screening: {
      ...(base?.screening ?? {
        topic: '',
        criteria_markdown: '',
        inclusion: [],
        exclusion: [],
        model: null,
        batch_size: 10,
        target_include_count: null,
        stop_when_target_reached: false,
        min_include_confidence: 0.8,
        allow_uncertain: true,
        retry_times: 6,
        request_timeout_seconds: 240,
        encoding: 'auto'
      }),
      topic: '',
      criteria_markdown: '',
      inclusion: [],
      exclusion: []
    },
    last_updated_at: base?.last_updated_at ?? threadUpdatedAt
  }
}

async function createThread() {
  if (!canCreateThread.value) {
    message.warning('先输入研究需求，再创建线程。')
    return
  }
  creatingThread.value = true
  try {
    const created = await projectsStore.createProject({
      name: resolvedThreadName.value,
      topic: resolvedProjectTopic.value,
      description: resolvedThreadDescription.value
    })
    const baseProfile = created.thread_profile ?? null
    await projectsStore.updateProjectWorkflow(created.id, {
      name: resolvedThreadName.value,
      topic: resolvedProjectTopic.value,
      description: resolvedThreadDescription.value,
      thread_profile: buildThreadProfile(baseProfile, created.updated_at)
    })
    draftsStore.clearStrategyDraft()
    message.success('线程已创建')
    await router.push(`/threads/${created.id}`)
  } catch (error) {
    const detail = (error as { response?: { data?: { detail?: unknown } } } | null)?.response?.data?.detail
    message.error(typeof detail === 'string' && detail ? detail : '线程创建失败')
  } finally {
    creatingThread.value = false
  }
}

watch([newProjectName, newProjectDescription, researchNeed], persistDraft)

onMounted(async () => {
  draftsStore.hydrate()
  await projectsStore.refreshProjects()
  if (draftsStore.strategyDraft.researchNeed.trim()) {
    draftNoticeDismissed.value = false
  }
})
</script>

<template>
  <div class="thread-new-view">
    <section class="thread-hero panel-surface">
      <div>
        <div class="eyebrow">Thread Kickoff</div>
        <h1>先输入研究需求，创建线程</h1>
        <p>这里只创建线程。主题、标准和检索方案都放到线程里继续处理。</p>
      </div>
      <div class="hero-actions">
        <RouterLink to="/">
          <NButton tertiary>返回线程列表</NButton>
        </RouterLink>
      </div>
    </section>

    <div class="thread-grid">
      <NCard title="研究需求与线程信息" class="panel-surface card-span-2">
        <NForm label-placement="top">
          <NFormItem label="线程名称">
            <NInput v-model:value="newProjectName" placeholder="可选，不填会自动生成" />
          </NFormItem>
          <NFormItem label="线程备注">
            <NInput
              v-model:value="newProjectDescription"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 5 }"
              placeholder="可选"
            />
          </NFormItem>
          <NFormItem label="研究需求">
            <NInput
              v-model:value="researchNeed"
              type="textarea"
              :autosize="{ minRows: 12, maxRows: 18 }"
              placeholder="直接描述你的研究需求"
            />
          </NFormItem>
        </NForm>

        <div v-if="draftsStore.hasStrategyDraft && !draftNoticeDismissed" class="draft-restore-block">
          <div class="action-copy">发现未提交草稿</div>
          <div class="draft-restore-actions">
            <NButton tertiary @click="restoreDraft">恢复旧草稿</NButton>
            <NButton tertiary @click="discardDraft">清空旧草稿</NButton>
          </div>
        </div>
      </NCard>

      <NCard title="下一步" class="panel-surface">
        <div class="next-step-list">
          <div class="next-step-item">
            <Wand2 :size="18" />
            <div>
              <div class="next-step-title">AI 识别主题与筛选条件</div>
              <div class="next-step-copy">在线程里一键填入主题、纳入和排除标准。</div>
            </div>
          </div>
          <div class="next-step-item">
            <Sparkles :size="18" />
            <div>
              <div class="next-step-title">生成检索方案</div>
              <div class="next-step-copy">生成检索词和完整方案。</div>
            </div>
          </div>
          <div class="next-step-item">
            <FileSearch :size="18" />
            <div>
              <div class="next-step-title">手动编辑主题与标准</div>
              <div class="next-step-copy">直接手动填写主题和标准。</div>
            </div>
          </div>
        </div>
      </NCard>

      <NCard title="将要创建的线程" class="panel-surface">
        <div class="preview-grid">
          <div>
            <div class="preview-label">线程名称</div>
            <div class="preview-value">{{ resolvedThreadName }}</div>
          </div>
          <div>
            <div class="preview-label">初始展示标题</div>
            <div class="preview-value">{{ resolvedProjectTopic }}</div>
          </div>
          <div>
            <div class="preview-label">默认状态</div>
            <div class="preview-value">等待在线程里继续补全主题和标准</div>
          </div>
        </div>
      </NCard>
    </div>

    <section class="footer-actions panel-surface">
      <div>
        <div class="action-title">先建线程</div>
        <div class="action-copy">后续步骤都在线程里完成。</div>
      </div>
      <NButton type="primary" size="large" :loading="creatingThread" :disabled="!canCreateThread" @click="createThread">
        创建线程
        <template #icon><ArrowRight :size="16" /></template>
      </NButton>
    </section>
  </div>
</template>

<style scoped>
.thread-new-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.thread-hero,
.footer-actions {
  border-radius: 24px;
}

.thread-hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 28px;
  background:
    radial-gradient(circle at top left, rgba(151, 176, 123, 0.22), transparent 46%),
    linear-gradient(135deg, rgba(248, 245, 236, 0.98), rgba(241, 236, 221, 0.94));
}

.thread-hero h1 {
  margin: 10px 0 12px;
  font-size: 32px;
  line-height: 1.2;
}

.thread-hero p {
  margin: 0;
  max-width: 760px;
  color: rgba(37, 40, 34, 0.76);
}

.hero-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 360px;
  min-width: 280px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 12px;
  font-weight: 700;
  color: rgba(52, 73, 42, 0.72);
}

.thread-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 20px;
}

.card-span-2 {
  grid-column: span 2;
}

.draft-restore-actions,
.preview-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.next-step-list {
  display: grid;
  gap: 14px;
}

.next-step-item {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr);
  gap: 12px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(248, 246, 239, 0.88);
  border: 1px solid rgba(82, 96, 64, 0.08);
  color: rgba(37, 40, 34, 0.78);
}

.next-step-title,
.action-title,
.preview-label {
  font-weight: 700;
  color: #2b3627;
}

.next-step-copy,
.action-copy,
.preview-value {
  color: rgba(37, 40, 34, 0.72);
}

.footer-actions {
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  background: linear-gradient(135deg, rgba(249, 247, 240, 0.96), rgba(241, 237, 224, 0.94));
}

@media (max-width: 1100px) {
  .thread-hero,
  .footer-actions {
    display: flex;
    flex-direction: column;
  }

  .hero-actions {
    width: 100%;
    min-width: 0;
  }

  .thread-grid {
    grid-template-columns: 1fr;
  }

  .card-span-2 {
    grid-column: auto;
  }
}
</style>
