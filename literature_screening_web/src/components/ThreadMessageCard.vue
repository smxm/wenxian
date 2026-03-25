<script setup lang="ts">
import dayjs from 'dayjs'
import { ArrowRight, Compass, Download, FileClock, FileSearch, FileText } from 'lucide-vue-next'
import { NButton, NCard, NProgress, NSpace, NTag, NText } from 'naive-ui'
import StatusPill from '@/components/StatusPill.vue'
import type { ThreadAction, ThreadMessage } from '@/types/thread'

const props = defineProps<{
  message: ThreadMessage
}>()

function progressOf(message: ThreadMessage) {
  if (!message.progressTotal || message.progressTotal <= 0 || message.progressCurrent === null || message.progressCurrent === undefined) {
    return null
  }
  return Math.max(0, Math.min(100, Math.round((message.progressCurrent / message.progressTotal) * 100)))
}

function iconFor(kind: ThreadMessage['kind']) {
  if (kind === 'strategy') return Compass
  return kind === 'screening' ? FileSearch : FileText
}

function buttonType(action: ThreadAction) {
  if (action.emphasis === 'primary') return 'primary'
  if (action.emphasis === 'report') return 'warning'
  if (action.emphasis === 'secondary') return 'success'
  return 'default'
}

function buttonSecondary(action: ThreadAction) {
  return action.emphasis !== 'primary' && action.emphasis !== 'report'
}

function actionIcon(action: ThreadAction) {
  if (action.kind === 'download') return Download
  if (action.emphasis === 'report') return FileText
  return ArrowRight
}
</script>

<template>
  <div class="thread-message">
    <div class="message-rail">
      <div class="message-dot" :class="`kind-${message.kind}`">
        <component :is="iconFor(message.kind)" :size="18" />
      </div>
      <div class="message-line" />
    </div>

    <NCard class="message-card panel-surface" :class="`kind-${message.kind}`" embedded>
      <template #header>
        <div class="message-header">
          <div>
            <div class="message-eyebrow">{{ message.eyebrow }}</div>
            <div class="message-title">{{ message.title }}</div>
          </div>
          <StatusPill :status="message.status" />
        </div>
      </template>

      <div class="message-meta">
        <span>{{ dayjs(message.createdAt).format('YYYY-MM-DD HH:mm') }}</span>
        <span v-if="message.phaseLabel">阶段：{{ message.phaseLabel }}</span>
        <span>来源：{{ message.sourceLabel }}</span>
      </div>

      <p class="message-body">{{ message.body }}</p>

      <div class="message-note" v-if="message.note">
        <FileClock :size="15" />
        <span>{{ message.note }}</span>
      </div>

      <div class="message-metrics" v-if="message.metrics.length">
        <NTag v-for="metric in message.metrics" :key="metric.label" size="small" round>
          {{ metric.label }} {{ metric.value }}
        </NTag>
      </div>

      <NProgress
        v-if="progressOf(message) !== null"
        class="message-progress"
        type="line"
        :percentage="progressOf(message) || 0"
        :indicator-placement="'inside'"
        processing
      />

      <div class="message-actions" v-if="message.actions.length">
        <NSpace wrap>
          <template v-for="action in message.actions" :key="action.id">
            <RouterLink v-if="action.kind === 'route' && action.to" :to="action.to">
              <NButton :type="buttonType(action)" :secondary="buttonSecondary(action)" :disabled="action.disabled">
                <template #icon>
                  <component :is="actionIcon(action)" :size="15" />
                </template>
                {{ action.label }}
              </NButton>
            </RouterLink>
            <NButton
              v-else-if="action.kind === 'download' && action.href"
              :type="buttonType(action)"
              :secondary="buttonSecondary(action)"
              :disabled="action.disabled"
              tag="a"
              :href="action.href"
              target="_blank"
              download
            >
              <template #icon>
                <Download :size="15" />
              </template>
              {{ action.label }}
            </NButton>
          </template>
        </NSpace>
      </div>
    </NCard>
  </div>
</template>

<style scoped>
.thread-message {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 14px;
}

.message-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.message-dot {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(135deg, #2d6a4f 0%, #7ea584 100%);
  box-shadow: 0 10px 22px rgba(45, 106, 79, 0.24);
}

.message-dot.kind-strategy {
  background: linear-gradient(135deg, #46677a 0%, #8ea7b5 100%);
  box-shadow: 0 10px 22px rgba(70, 103, 122, 0.2);
}

.message-dot.kind-report {
  background: linear-gradient(135deg, #9a6a17 0%, #d2a34e 100%);
  box-shadow: 0 10px 22px rgba(154, 106, 23, 0.2);
}

.message-line {
  flex: 1;
  width: 2px;
  margin-top: 8px;
  background: linear-gradient(180deg, rgba(45, 106, 79, 0.35), rgba(45, 106, 79, 0.04));
}

.message-card {
  border-radius: 22px;
}

.message-card.kind-screening {
  border-color: rgba(45, 106, 79, 0.16);
}

.message-card.kind-report {
  border-color: rgba(196, 137, 29, 0.26);
  background: rgba(255, 250, 241, 0.9);
}

.message-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.message-eyebrow {
  font-size: 12px;
  color: #6a776c;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.message-title {
  margin-top: 6px;
  font-size: 20px;
  font-weight: 700;
  line-height: 1.35;
}

.message-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  color: #617065;
  font-size: 13px;
}

.message-body {
  margin: 14px 0 0;
  color: #2b332d;
  line-height: 1.75;
}

.message-note {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  align-items: center;
  color: #6a776c;
  font-size: 13px;
}

.message-metrics {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.message-progress {
  margin-top: 16px;
}

.message-actions {
  margin-top: 18px;
}

@media (max-width: 900px) {
  .thread-message {
    grid-template-columns: 1fr;
  }

  .message-rail {
    display: none;
  }
}
</style>
