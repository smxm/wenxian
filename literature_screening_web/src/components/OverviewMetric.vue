<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  caption?: string
}>()
</script>

<template>
  <div class="metric-card panel-surface">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value">{{ value }}</div>
    <div v-if="caption" class="metric-caption">{{ caption }}</div>
  </div>
</template>

<style scoped>
.metric-card {
  padding: 18px;
}

.metric-label {
  color: #657168;
  font-size: 13px;
}

.metric-value {
  margin-top: 10px;
  font-size: 34px;
  line-height: 1;
  font-weight: 800;
  color: #1f2520;
}

.metric-caption {
  margin-top: 10px;
  color: #6f796f;
  font-size: 12px;
}
</style>
