<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import dayjs from 'dayjs'
import { ArrowLeft, FileText, RefreshCw, Search } from 'lucide-vue-next'
import {
  NAlert,
  NButton,
  NCard,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSpin,
  NTag,
  useMessage
} from 'naive-ui'
import { useProjectsStore } from '@/stores/projects'
import type { DatasetRecord, FulltextStatus, TaskSnapshot } from '@/types/api'

const route = useRoute()
const message = useMessage()
const projectsStore = useProjectsStore()

const projectId = computed(() => String(route.params.projectId))
const project = computed(() => projectsStore.currentProject)

const searchKeyword = ref('')
const activeStatusFilter = ref<'all' | FulltextStatus>('all')
const fulltextSourceDatasetIds = ref<string[]>([])
const fulltextNotes = ref<Record<string, string>>({})
const updatingPaperId = ref<string | null>(null)
const updatingStatus = ref<FulltextStatus | null>(null)
const lastUpdatedPaperId = ref<string | null>(null)
const lastActionText = ref('')
const rebuildingQueue = ref(false)
const enrichingQueue = ref(false)

const datasetMap = computed(() => {
  const map = new Map<string, DatasetRecord>()
  for (const dataset of project.value?.datasets ?? []) {
    map.set(dataset.id, dataset)
  }
  return map
})

const screeningRounds = computed(() =>
  [...(project.value?.tasks ?? [])]
    .filter((task) => task.kind === 'screening')
    .sort((a, b) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf())
)
const cumulativeIncludedDataset = computed(() =>
  (project.value?.datasets ?? []).find((dataset) => dataset.kind === 'cumulative_included') ?? null
)
const fulltextReadyDataset = computed(() =>
  (project.value?.datasets ?? []).find((dataset) => dataset.kind === 'fulltext_ready') ?? null
)
const fulltextQueue = computed(() => project.value?.fulltext_queue ?? [])

function latestMatchingDataset(task: TaskSnapshot, kinds: string[]) {
  const matches = task.output_dataset_ids
    .map((datasetId) => datasetMap.value.get(datasetId) ?? null)
    .filter((dataset): dataset is DatasetRecord => Boolean(dataset && kinds.includes(dataset.kind)))
  return matches.length ? matches[matches.length - 1] : null
}

const fulltextSourceOptions = computed(() => {
  const options: Array<{ label: string; value: string }> = []
  const pushOnce = (dataset: DatasetRecord | null, label: string) => {
    if (!dataset) return
    if (options.some((item) => item.value === dataset.id)) return
    options.push({
      label: `${label} · ${dataset.record_count ?? '-'} 篇`,
      value: dataset.id
    })
  }
  pushOnce(cumulativeIncludedDataset.value, '项目累计纳入')
  for (const round of [...screeningRounds.value].reverse()) {
    const includedDataset = latestMatchingDataset(round, ['included_reviewed', 'included'])
    const roundIndex = screeningRounds.value.findIndex((item) => item.id === round.id) + 1
    pushOnce(includedDataset, `第 ${roundIndex} 轮纳入`)
  }
  return options
})

const fulltextCounts = computed(() => {
  const counts = { pending: 0, ready: 0, unavailable: 0, deferred: 0 }
  for (const item of fulltextQueue.value) counts[item.status] += 1
  return counts
})

const filteredQueue = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return fulltextQueue.value.filter((item) => {
    if (activeStatusFilter.value !== 'all' && item.status !== activeStatusFilter.value) return false
    if (!keyword) return true
    const haystack = [item.title, item.journal, item.doi, item.year]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return haystack.includes(keyword)
  })
})

const sourceSelectionDirty = computed(() => {
  const current = [...fulltextSourceDatasetIds.value].sort()
  const server = [...(project.value?.fulltext_source_dataset_ids ?? [])].sort()
  if (current.length !== server.length) return true
  return current.some((item, index) => item !== server[index])
})

const readyReportRoute = computed(() => {
  if (!project.value || !fulltextReadyDataset.value || (fulltextReadyDataset.value.record_count ?? 0) <= 0) return null
  return {
    path: `/threads/${project.value.id}`,
    query: { reportDatasetId: fulltextReadyDataset.value.id }
  }
})

function initializeLocalState() {
  if (!project.value) return
  if ((project.value.fulltext_source_dataset_ids ?? []).length) {
    fulltextSourceDatasetIds.value = [...project.value.fulltext_source_dataset_ids]
  } else if (fulltextSourceOptions.value.length) {
    fulltextSourceDatasetIds.value = [fulltextSourceOptions.value[0].value]
  } else {
    fulltextSourceDatasetIds.value = []
  }
  fulltextNotes.value = Object.fromEntries(fulltextQueue.value.map((item) => [item.paper_id, item.note ?? '']))
}

function statusLabel(status: FulltextStatus) {
  switch (status) {
    case 'ready':
      return '已获取全文'
    case 'unavailable':
      return '无权限获取'
    case 'deferred':
      return '暂缓'
    default:
      return '未处理'
  }
}

function statusTagType(status: FulltextStatus) {
  switch (status) {
    case 'ready':
      return 'success'
    case 'unavailable':
      return 'error'
    case 'deferred':
      return 'warning'
    default:
      return undefined
  }
}

function sourceSummary() {
  const labels = fulltextSourceDatasetIds.value
    .map((datasetId) => fulltextSourceOptions.value.find((item) => item.value === datasetId)?.label ?? '')
    .filter(Boolean)
  return labels.join('、')
}

function filterSummary() {
  const parts = [`当前显示 ${filteredQueue.value.length} / ${fulltextQueue.value.length} 篇`]
  if (activeStatusFilter.value !== 'all') parts.push(`状态：${statusLabel(activeStatusFilter.value)}`)
  if (searchKeyword.value.trim()) parts.push(`检索：${searchKeyword.value.trim()}`)
  return parts.join(' · ')
}

function extractErrorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } } | null)?.response?.data?.detail
  if (typeof detail === 'string' && detail) return detail
  const messageText = (error as { message?: unknown } | null)?.message
  if (typeof messageText === 'string' && messageText) return messageText
  return fallback
}

async function loadProject() {
  await projectsStore.loadProject(projectId.value)
  initializeLocalState()
  const requestedStatus = route.query.status
  if (requestedStatus === 'pending' || requestedStatus === 'ready' || requestedStatus === 'unavailable' || requestedStatus === 'deferred') {
    activeStatusFilter.value = requestedStatus
  } else {
    activeStatusFilter.value = 'all'
  }
}

watch(projectId, async () => {
  searchKeyword.value = ''
  activeStatusFilter.value = 'all'
  lastUpdatedPaperId.value = null
  lastActionText.value = ''
  await loadProject()
}, { immediate: true })

watch(project, () => {
  initializeLocalState()
})

async function rebuildThreadFulltextQueue() {
  if (!project.value) return
  rebuildingQueue.value = true
  try {
    await projectsStore.rebuildFulltextQueue(project.value.id, [...fulltextSourceDatasetIds.value])
    initializeLocalState()
    lastActionText.value = sourceSummary()
      ? `已按“${sourceSummary()}”重建全文获取队列。`
      : '全文获取队列已更新。'
    message.success('全文获取队列已更新')
  } catch (error) {
    message.error(extractErrorMessage(error, '全文获取队列更新失败'))
  } finally {
    rebuildingQueue.value = false
  }
}

async function enrichThreadFulltextQueue() {
  if (!project.value) return
  enrichingQueue.value = true
  try {
    await projectsStore.enrichFulltextQueue(project.value.id)
    initializeLocalState()
    lastActionText.value = '已刷新 DOI 落地页与 OA / PDF 链接。'
    message.success('已刷新 DOI 落地页和 OA 链接')
  } catch (error) {
    message.error(extractErrorMessage(error, 'OA / 链接刷新失败'))
  } finally {
    enrichingQueue.value = false
  }
}

async function updateThreadFulltextStatus(item: { paper_id: string; title: string; note?: string; status: FulltextStatus }, status: FulltextStatus) {
  if (!project.value) return
  updatingPaperId.value = item.paper_id
  updatingStatus.value = status
  try {
    await projectsStore.updateFulltextStatus(project.value.id, {
      paper_id: item.paper_id,
      status,
      note: fulltextNotes.value[item.paper_id] ?? item.note ?? ''
    })
    initializeLocalState()
    lastUpdatedPaperId.value = item.paper_id
    lastActionText.value = `已将《${item.title}》标记为“${statusLabel(status)}”。`
    message.success(`${statusLabel(status)} 已保存`)
  } catch (error) {
    message.error(extractErrorMessage(error, '全文状态保存失败'))
  } finally {
    updatingPaperId.value = null
    updatingStatus.value = null
  }
}

async function copyDoi(doi?: string | null) {
  if (!doi) return
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(doi)
  } else {
    const input = document.createElement('input')
    input.value = doi
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
  }
  message.success('DOI 已复制')
}

function openExternal(url?: string | null) {
  if (!url) return
  window.open(url, '_blank', 'noopener')
}
</script>

<template>
  <div class="fulltext-page">
    <NSpin :show="projectsStore.loadingDetail && !project">
      <div v-if="project" class="fulltext-stack">
        <section class="fulltext-hero">
          <div class="hero-main">
            <div class="eyebrow">Full-text Workspace</div>
            <h1>全文获取工作台</h1>
            <p>{{ project.name }}：把全文标记、筛选和链接检查集中到一个页面里处理，不再挤在报告面板下面。</p>
          </div>
          <div class="hero-actions">
            <RouterLink :to="`/threads/${project.id}`">
              <NButton secondary>
                <template #icon><ArrowLeft :size="16" /></template>
                返回主题页
              </NButton>
            </RouterLink>
            <RouterLink v-if="readyReportRoute" :to="readyReportRoute">
              <NButton type="primary">
                <template #icon><FileText :size="16" /></template>
                用已获取全文生成报告
              </NButton>
            </RouterLink>
          </div>
        </section>

        <NCard class="panel-surface workspace-card" embedded>
          <div class="workspace-head">
            <div>
              <div class="workspace-title">队列控制台</div>
              <div class="workspace-copy">点击统计标签即可筛选；修改备注后，点击任一状态按钮会连同备注一起保存。</div>
            </div>
            <div class="workspace-meta">{{ filterSummary() }}</div>
          </div>

          <NAlert v-if="lastActionText" type="success" :show-icon="false" class="workspace-alert">
            {{ lastActionText }}
          </NAlert>

          <div class="summary-chips">
            <button
              class="summary-chip"
              :class="{ active: activeStatusFilter === 'all' }"
              type="button"
              @click="activeStatusFilter = 'all'"
            >
              全部 {{ fulltextQueue.length }}
            </button>
            <button
              class="summary-chip"
              :class="{ active: activeStatusFilter === 'pending' }"
              type="button"
              @click="activeStatusFilter = 'pending'"
            >
              未处理 {{ fulltextCounts.pending }}
            </button>
            <button
              class="summary-chip success"
              :class="{ active: activeStatusFilter === 'ready' }"
              type="button"
              @click="activeStatusFilter = 'ready'"
            >
              已获取 {{ fulltextCounts.ready }}
            </button>
            <button
              class="summary-chip error"
              :class="{ active: activeStatusFilter === 'unavailable' }"
              type="button"
              @click="activeStatusFilter = 'unavailable'"
            >
              无权限 {{ fulltextCounts.unavailable }}
            </button>
            <button
              class="summary-chip warning"
              :class="{ active: activeStatusFilter === 'deferred' }"
              type="button"
              @click="activeStatusFilter = 'deferred'"
            >
              暂缓 {{ fulltextCounts.deferred }}
            </button>
          </div>

          <div class="control-grid">
            <NForm label-placement="top" class="control-card">
              <NFormItem label="来源">
                <NSelect v-model:value="fulltextSourceDatasetIds" multiple :options="fulltextSourceOptions" />
              </NFormItem>
              <div class="control-actions">
                <NButton :type="sourceSelectionDirty ? 'primary' : 'default'" :loading="rebuildingQueue" :disabled="!fulltextSourceDatasetIds.length || enrichingQueue" @click="rebuildThreadFulltextQueue">
                  更新队列
                </NButton>
                <NButton secondary :loading="enrichingQueue" :disabled="rebuildingQueue" @click="enrichThreadFulltextQueue">
                  <template #icon><RefreshCw :size="16" /></template>
                  刷新 OA / 链接
                </NButton>
              </div>
              <div v-if="sourceSelectionDirty" class="control-hint">来源已改动，点击“更新队列”后才会重建列表和“仅已获取全文”数据集。</div>
            </NForm>

            <NForm label-placement="top" class="control-card">
              <NFormItem label="搜索">
                <NInput v-model:value="searchKeyword" placeholder="按标题、期刊、DOI 或年份过滤">
                  <template #prefix>
                    <Search :size="16" />
                  </template>
                </NInput>
              </NFormItem>
              <div class="control-note">
                <span>当前来源</span>
                <strong>{{ sourceSummary() || '尚未选择' }}</strong>
              </div>
              <div class="control-note">
                <span>报告可用全文</span>
                <strong>{{ fulltextReadyDataset?.record_count ?? 0 }} 篇</strong>
              </div>
            </NForm>
          </div>
        </NCard>

        <div v-if="filteredQueue.length" class="queue-list">
          <article
            v-for="item in filteredQueue"
            :key="item.paper_id"
            class="queue-item panel-surface"
            :class="{ highlighted: lastUpdatedPaperId === item.paper_id }"
          >
            <div class="queue-item-head">
              <div>
                <h2>{{ item.title }}</h2>
                <div class="queue-item-meta">{{ item.journal || '未知期刊' }}</div>
              </div>
              <div class="queue-item-tags">
                <NTag round size="small" :type="statusTagType(item.status)">{{ statusLabel(item.status) }}</NTag>
                <NTag v-if="item.oa_status" round size="small">{{ item.oa_status === 'oa' ? 'OA' : item.oa_status }}</NTag>
                <NTag round size="small">{{ item.year ?? '----' }}</NTag>
              </div>
            </div>

            <div class="queue-item-links">
              <NButton text size="small" :disabled="!item.doi_url" @click="openExternal(item.doi_url)">打开 DOI</NButton>
              <NButton text size="small" :disabled="!item.doi" @click="copyDoi(item.doi)">复制 DOI</NButton>
              <NButton text size="small" :disabled="!item.landing_url" @click="openExternal(item.landing_url)">打开落地页</NButton>
              <NButton text size="small" :disabled="!item.pdf_url" @click="openExternal(item.pdf_url)">打开 PDF</NButton>
            </div>

            <div class="queue-item-updated">最近更新：{{ dayjs(item.updated_at).format('YYYY-MM-DD HH:mm') }}</div>

            <NInput
              v-model:value="fulltextNotes[item.paper_id]"
              type="textarea"
              :disabled="updatingPaperId === item.paper_id"
              placeholder="备注：例如已在 Zotero 保存 / 通过机构权限获取 / 稍后再处理"
              :autosize="{ minRows: 1, maxRows: 3 }"
            />

            <div class="queue-item-actions">
              <NButton
                size="small"
                :secondary="item.status !== 'pending'"
                :disabled="updatingPaperId === item.paper_id && updatingStatus !== 'pending'"
                :loading="updatingPaperId === item.paper_id && updatingStatus === 'pending'"
                @click="updateThreadFulltextStatus(item, 'pending')"
              >
                未处理
              </NButton>
              <NButton
                size="small"
                type="success"
                :secondary="item.status !== 'ready'"
                :disabled="updatingPaperId === item.paper_id && updatingStatus !== 'ready'"
                :loading="updatingPaperId === item.paper_id && updatingStatus === 'ready'"
                @click="updateThreadFulltextStatus(item, 'ready')"
              >
                已获取全文
              </NButton>
              <NButton
                size="small"
                type="error"
                :secondary="item.status !== 'unavailable'"
                :disabled="updatingPaperId === item.paper_id && updatingStatus !== 'unavailable'"
                :loading="updatingPaperId === item.paper_id && updatingStatus === 'unavailable'"
                @click="updateThreadFulltextStatus(item, 'unavailable')"
              >
                无权限获取
              </NButton>
              <NButton
                size="small"
                type="warning"
                :secondary="item.status !== 'deferred'"
                :disabled="updatingPaperId === item.paper_id && updatingStatus !== 'deferred'"
                :loading="updatingPaperId === item.paper_id && updatingStatus === 'deferred'"
                @click="updateThreadFulltextStatus(item, 'deferred')"
              >
                暂缓
              </NButton>
            </div>
          </article>
        </div>
        <NEmpty v-else class="panel-surface empty-state" :description="searchKeyword || activeStatusFilter !== 'all' ? '当前筛选条件下没有匹配文献' : '先选择一组纳入结果并更新全文获取队列'" />
      </div>

      <NEmpty v-else class="panel-surface empty-state" description="主题不存在或仍在加载中" />
    </NSpin>
  </div>
</template>

<style scoped>
.fulltext-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.fulltext-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.fulltext-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px 24px;
  align-items: end;
  padding: 4px 0 2px;
  border-bottom: 1px solid rgba(90, 107, 93, 0.12);
}

.eyebrow {
  font-size: 12px;
  color: #6a776c;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.hero-main h1 {
  margin: 10px 0 8px;
  font-size: 34px;
  line-height: 1.12;
}

.hero-main p {
  margin: 0;
  color: #526055;
  line-height: 1.7;
  max-width: 880px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
  justify-self: end;
}

.workspace-card {
  border-radius: 24px;
}

.workspace-head {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
}

.workspace-title {
  font-size: 22px;
  font-weight: 700;
}

.workspace-copy,
.workspace-meta {
  margin-top: 6px;
  color: #526055;
  line-height: 1.6;
}

.workspace-meta {
  white-space: nowrap;
}

.workspace-alert {
  margin-top: 14px;
}

.summary-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 16px 0 0;
}

.summary-chip {
  border: 1px solid rgba(95, 108, 98, 0.18);
  background: rgba(255, 255, 255, 0.72);
  color: #304036;
  border-radius: 999px;
  padding: 9px 14px;
  font-size: 14px;
  cursor: pointer;
  transition: transform 140ms ease, border-color 140ms ease, background 140ms ease, box-shadow 140ms ease;
}

.summary-chip:hover {
  transform: translateY(-1px);
  border-color: rgba(45, 106, 79, 0.28);
}

.summary-chip.active {
  box-shadow: 0 10px 22px rgba(45, 106, 79, 0.14);
  border-color: rgba(45, 106, 79, 0.48);
  background: rgba(45, 106, 79, 0.12);
}

.summary-chip.success.active {
  background: rgba(47, 133, 90, 0.14);
  border-color: rgba(47, 133, 90, 0.42);
}

.summary-chip.error.active {
  background: rgba(192, 86, 33, 0.14);
  border-color: rgba(192, 86, 33, 0.42);
}

.summary-chip.warning.active {
  background: rgba(196, 137, 29, 0.14);
  border-color: rgba(196, 137, 29, 0.42);
}

.control-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.9fr);
  gap: 16px;
  margin-top: 18px;
}

.control-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(90, 107, 93, 0.12);
  background: rgba(255, 255, 255, 0.58);
}

.control-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.control-hint {
  margin-top: 10px;
  color: #8a5b1f;
  line-height: 1.6;
}

.control-note {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #506055;
  line-height: 1.6;
}

.control-note + .control-note {
  margin-top: 10px;
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.queue-item {
  padding: 18px;
  border-radius: 24px;
  transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
}

.queue-item.highlighted {
  border-color: rgba(45, 106, 79, 0.45);
  box-shadow: 0 18px 36px rgba(45, 106, 79, 0.12);
}

.queue-item-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.queue-item-head h2 {
  margin: 0;
  font-size: 20px;
  line-height: 1.45;
}

.queue-item-meta,
.queue-item-updated {
  color: #526055;
}

.queue-item-meta {
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.6;
}

.queue-item-updated {
  margin: 12px 0;
  font-size: 13px;
}

.queue-item-tags,
.queue-item-links,
.queue-item-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.queue-item-links {
  margin-top: 14px;
}

.queue-item-actions {
  margin-top: 14px;
}

.empty-state {
  min-height: 180px;
  display: grid;
  place-items: center;
}

@media (max-width: 1080px) {
  .workspace-head {
    flex-direction: column;
  }

  .fulltext-hero {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .hero-actions {
    justify-self: start;
    justify-content: flex-start;
  }

  .workspace-meta {
    white-space: normal;
  }

  .control-grid {
    grid-template-columns: 1fr;
  }
}
</style>
