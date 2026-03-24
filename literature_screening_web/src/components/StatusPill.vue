<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const label = computed(() => {
  const mapping: Record<string, string> = {
    pending: '待开始',
    running: '运行中',
    succeeded: '已完成',
    failed: '失败',
    cancelled: '已停止'
  }
  return mapping[props.status] ?? props.status
})

const tone = computed(() => {
  const mapping: Record<string, string> = {
    pending: 'tone-pending',
    running: 'tone-running',
    succeeded: 'tone-succeeded',
    failed: 'tone-failed',
    cancelled: 'tone-cancelled'
  }
  return mapping[props.status] ?? 'tone-pending'
})
</script>

<template>
  <span class="status-pill" :class="tone">{{ label }}</span>
</template>

<style scoped>
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.tone-pending {
  background: rgba(207, 179, 114, 0.18);
  color: #8a6112;
}

.tone-running {
  background: rgba(45, 106, 79, 0.16);
  color: #27503d;
}

.tone-succeeded {
  background: rgba(79, 138, 86, 0.16);
  color: #205739;
}

.tone-failed {
  background: rgba(192, 86, 33, 0.14);
  color: #963b10;
}

.tone-cancelled {
  background: rgba(97, 90, 77, 0.16);
  color: #574f40;
}
</style>
