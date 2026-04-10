<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { NDataTable, NInput, NSelect, NTabPane, NTabs, NText } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { ScreeningRecordRow } from '@/types/api'

const props = defineProps<{
  rows: ScreeningRecordRow[]
  activePaperId?: string | null
  selectedPaperIds?: string[]
}>()

const emit = defineEmits<{
  select: [row: ScreeningRecordRow]
  selectionChange: [paperIds: string[]]
}>()

const filter = ref('')
const activeTab = ref<'all' | 'include' | 'exclude' | 'uncertain'>('all')
const yearFilter = ref<number | null>(null)
const sortMode = ref<'relevance' | 'year-desc' | 'year-asc'>('relevance')

const yearOptions = computed(() => {
  const years = Array.from(new Set(props.rows.map((row) => row.year).filter((year): year is number => typeof year === 'number')))
    .sort((a, b) => b - a)
  return years.map((year) => ({ label: String(year), value: year }))
})

const columns: DataTableColumns<ScreeningRecordRow> = [
  {
    type: 'selection',
    multiple: true,
    width: 48
  },
  {
    title: '标题',
    key: 'title',
    minWidth: 300,
    render: row => h('div', { style: 'white-space: normal;' }, row.title)
  },
  {
    title: '相关度',
    key: 'confidence',
    width: 92,
    render: row => {
      const value = confidenceNumber(row.confidence)
      if (value === null) return '-'
      return `${Math.round(value * 100)}%`
    }
  },
  {
    title: '年份',
    key: 'year',
    width: 86
  },
  {
    title: '期刊',
    key: 'journal',
    minWidth: 160
  },
  {
    title: '理由',
    key: 'reason',
    minWidth: 300,
    render: row => h(NText, { depth: 3 }, { default: () => row.reason || '-' })
  }
]

function confidenceNumber(value: ScreeningRecordRow['confidence']) {
  if (value === null || value === undefined || value === '') return null
  if (typeof value === 'number') return value
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function compareByRelevance(left: ScreeningRecordRow, right: ScreeningRecordRow) {
  const leftConfidence = confidenceNumber(left.confidence) ?? -1
  const rightConfidence = confidenceNumber(right.confidence) ?? -1
  if (rightConfidence !== leftConfidence) return rightConfidence - leftConfidence
  const leftYear = left.year ?? -Infinity
  const rightYear = right.year ?? -Infinity
  if (rightYear !== leftYear) return rightYear - leftYear
  return left.title.localeCompare(right.title)
}

const filteredRows = computed(() => {
  const keyword = filter.value.trim().toLowerCase()
  let rows = props.rows.filter((row) => {
    if (activeTab.value !== 'all' && row.decision !== activeTab.value) return false
    if (yearFilter.value !== null && row.year !== yearFilter.value) return false
    if (!keyword) return true
    return [row.title, row.reason, row.journal, row.doi]
      .filter(Boolean)
      .some((value) => value!.toLowerCase().includes(keyword))
  })
  rows = rows.slice().sort((a, b) => {
    if (sortMode.value === 'relevance') return compareByRelevance(a, b)

    const left = a.year ?? (sortMode.value === 'year-desc' ? -Infinity : Infinity)
    const right = b.year ?? (sortMode.value === 'year-desc' ? -Infinity : Infinity)
    const yearCompare = sortMode.value === 'year-desc' ? right - left : left - right
    if (yearCompare !== 0) return yearCompare
    return compareByRelevance(a, b)
  })
  return rows
})

const tabCount = computed(() => ({
  all: props.rows.length,
  include: props.rows.filter((row) => row.decision === 'include').length,
  exclude: props.rows.filter((row) => row.decision === 'exclude').length,
  uncertain: props.rows.filter((row) => row.decision === 'uncertain').length
}))

function rowProps(row: ScreeningRecordRow) {
  const active = row.paper_id === props.activePaperId
  return {
    onClick: () => emit('select', row),
    style: active ? 'cursor:pointer;background: rgba(95,122,102,0.08);' : 'cursor:pointer;'
  }
}
</script>

<template>
  <div class="records-shell">
    <div class="toolbar">
      <NInput v-model:value="filter" placeholder="筛选标题、理由、期刊或 DOI" clearable />
      <NSelect v-model:value="yearFilter" clearable :options="yearOptions" placeholder="年份筛选" />
      <NSelect
        v-model:value="sortMode"
        :options="[
          { label: '默认按相关度', value: 'relevance' },
          { label: '按年份从新到旧', value: 'year-desc' },
          { label: '按年份从旧到新', value: 'year-asc' }
        ]"
      />
    </div>
    <NTabs v-model:value="activeTab" type="segment">
      <NTabPane name="all" :tab="`全部 (${tabCount.all})`" />
      <NTabPane name="include" :tab="`纳入 (${tabCount.include})`" />
      <NTabPane name="exclude" :tab="`剔除 (${tabCount.exclude})`" />
      <NTabPane name="uncertain" :tab="`不确定 (${tabCount.uncertain})`" />
    </NTabs>
    <NDataTable
      :columns="columns"
      :data="filteredRows"
      :pagination="{ pageSize: 10 }"
      :row-props="rowProps"
      :row-key="(row: ScreeningRecordRow) => row.paper_id"
      :checked-row-keys="selectedPaperIds ?? []"
      @update:checked-row-keys="(keys) => emit('selectionChange', keys as string[])"
    />
  </div>
</template>

<style scoped>
.records-shell {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(150px, 0.6fr) minmax(180px, 0.7fr);
  gap: 10px;
}

@media (max-width: 920px) {
  .toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
