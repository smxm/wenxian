<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { NDataTable, NInput, NTabPane, NTabs, NText } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { ScreeningRecordRow } from '@/types/api'

const props = defineProps<{
  rows: ScreeningRecordRow[]
}>()

const filter = ref('')

const columns: DataTableColumns<ScreeningRecordRow> = [
  {
    title: '标题',
    key: 'title',
    minWidth: 320,
    render: row => h('div', { style: 'white-space: normal;' }, row.title)
  },
  {
    title: '年份',
    key: 'year',
    width: 84
  },
  {
    title: '期刊',
    key: 'journal',
    minWidth: 180
  },
  {
    title: '理由',
    key: 'reason',
    minWidth: 360,
    render: row => h(NText, { depth: 3 }, { default: () => row.reason || '-' })
  }
]

const filteredRows = computed(() => {
  const keyword = filter.value.trim().toLowerCase()
  if (!keyword) return props.rows
  return props.rows.filter((row) => {
    return [row.title, row.reason, row.journal, row.doi].filter(Boolean).some((value) => value!.toLowerCase().includes(keyword))
  })
})

const groups = computed(() => ({
  include: filteredRows.value.filter(row => row.decision === 'include'),
  exclude: filteredRows.value.filter(row => row.decision === 'exclude'),
  uncertain: filteredRows.value.filter(row => row.decision === 'uncertain')
}))
</script>

<template>
  <div class="records-shell">
    <NInput v-model:value="filter" placeholder="筛选标题、理由或期刊" clearable />
    <NTabs type="segment">
      <NTabPane name="include" :tab="`纳入 (${groups.include.length})`">
        <NDataTable :columns="columns" :data="groups.include" :pagination="{ pageSize: 8 }" />
      </NTabPane>
      <NTabPane name="exclude" :tab="`剔除 (${groups.exclude.length})`">
        <NDataTable :columns="columns" :data="groups.exclude" :pagination="{ pageSize: 8 }" />
      </NTabPane>
      <NTabPane name="uncertain" :tab="`不确定 (${groups.uncertain.length})`">
        <NDataTable :columns="columns" :data="groups.uncertain" :pagination="{ pageSize: 8 }" />
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped>
.records-shell {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
</style>
