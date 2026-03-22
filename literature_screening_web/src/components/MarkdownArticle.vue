<script setup lang="ts">
import MarkdownIt from 'markdown-it'
import { computed } from 'vue'

const props = defineProps<{
  source: string
}>()

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

const rendered = computed(() => md.render(props.source || ''))
</script>

<template>
  <article class="markdown-article panel-surface" v-html="rendered" />
</template>

<style scoped>
.markdown-article {
  padding: 26px 30px;
  line-height: 1.8;
}

.markdown-article :deep(h1),
.markdown-article :deep(h2),
.markdown-article :deep(h3) {
  color: #1f2520;
  line-height: 1.3;
}

.markdown-article :deep(p),
.markdown-article :deep(li) {
  color: #445046;
}

.markdown-article :deep(pre) {
  overflow: auto;
  border-radius: 16px;
  padding: 16px;
  background: #f3efe6;
}
</style>
