<script setup lang="ts">
import { Download, FileText, FileJson, LibraryBig } from 'lucide-vue-next'
import { NButton, NCard, NEmpty, NSpace, NText } from 'naive-ui'
import { getArtifactUrl } from '@/api/client'
import type { TaskArtifact } from '@/types/api'

const props = defineProps<{
  taskId: string
  artifacts: TaskArtifact[]
}>()

function iconFor(filename: string) {
  if (filename.endsWith('.json')) return FileJson
  if (filename.endsWith('.ris') || filename.endsWith('.bib')) return LibraryBig
  return FileText
}

function fileSize(size?: number | null) {
  if (!size) return ''
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <div class="artifact-grid">
    <NCard v-for="artifact in artifacts" :key="artifact.key" class="artifact-card" embedded>
      <template #header>
        <div class="artifact-header">
          <component :is="iconFor(artifact.filename)" :size="18" />
          <div>
            <div class="artifact-name">{{ artifact.filename }}</div>
            <NText depth="3">{{ fileSize(artifact.size_bytes) }}</NText>
          </div>
        </div>
      </template>

      <NButton
        secondary
        type="primary"
        tag="a"
        :href="getArtifactUrl(taskId, artifact.key)"
        :download="artifact.filename"
        block
      >
        <template #icon>
          <Download :size="16" />
        </template>
        下载
      </NButton>
    </NCard>

    <NEmpty
      v-if="!artifacts.length"
      description="当前任务还没有可下载文件。"
      class="panel-surface artifact-empty"
    />
  </div>
</template>

<style scoped>
.artifact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.artifact-card {
  border-radius: 20px;
}

.artifact-header {
  display: flex;
  gap: 12px;
  align-items: center;
}

.artifact-name {
  font-weight: 700;
  word-break: break-all;
}

.artifact-empty {
  padding: 22px;
}
</style>
