<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { CircleDashed, FileUp, WandSparkles } from 'lucide-vue-next'
import { NAlert, NButton, NCard, NCheckbox, NDynamicInput, NForm, NFormItem, NGrid, NGridItem, NInput, NInputNumber, NSelect, NSpace, NText } from 'naive-ui'
import { useMetaStore } from '@/stores/meta'
import { useTasksStore } from '@/stores/tasks'
import { parseCriteriaMarkdown } from '@/utils/criteria'
import type { ModelSettings, ProviderName } from '@/types/api'

const router = useRouter()
const metaStore = useMetaStore()
const tasksStore = useTasksStore()

const title = ref('new-screening-run')
const topic = ref('')
const inclusion = ref<string[]>([''])
const exclusion = ref<string[]>([''])
const criteriaMarkdown = ref('')
const provider = ref<ProviderName>('deepseek')
const model = ref<ModelSettings>({
  provider: 'deepseek',
  model_name: 'deepseek-chat',
  api_base_url: 'https://api.deepseek.com/v1',
  api_key_env: 'DEEPSEEK_API_KEY',
  temperature: 0,
  max_tokens: 1536,
  min_request_interval_seconds: 2
})
const batchSize = ref(20)
const targetIncludeCount = ref(30)
const stopWhenReached = ref(true)
const allowUncertain = ref(true)
const retryTimes = ref(6)
const requestTimeout = ref(240)
const encoding = ref('auto')
const files = ref<File[]>([])

const selectedPreset = computed(() => metaStore.providerPresets.find(item => item.provider === provider.value))

watch(provider, (nextProvider) => {
  const preset = metaStore.providerPresets.find(item => item.provider === nextProvider)
  if (!preset) return
  model.value = {
    provider: preset.provider,
    model_name: preset.defaultModel,
    api_base_url: preset.defaultBaseUrl,
    api_key_env: preset.defaultApiKeyEnv,
    temperature: model.value.temperature,
    max_tokens: model.value.max_tokens,
    min_request_interval_seconds: model.value.min_request_interval_seconds
  }
})

function parseCriteria() {
  const draft = parseCriteriaMarkdown(criteriaMarkdown.value)
  if (draft.topic) topic.value = draft.topic
  if (draft.inclusion.length) inclusion.value = draft.inclusion
  if (draft.exclusion.length) exclusion.value = draft.exclusion
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  files.value = Array.from(input.files ?? [])
}

async function submit() {
  const task = await tasksStore.submitScreening({
    title: title.value,
    topic: topic.value,
    inclusion: inclusion.value.filter(Boolean),
    exclusion: exclusion.value.filter(Boolean),
    model: model.value,
    batch_size: batchSize.value,
    target_include_count: targetIncludeCount.value,
    stop_when_target_reached: stopWhenReached.value,
    allow_uncertain: allowUncertain.value,
    retry_times: retryTimes.value,
    request_timeout_seconds: requestTimeout.value,
    encoding: encoding.value,
    files: files.value
  })
  await router.push(`/tasks/${task.id}`)
}

const canSubmit = computed(() => {
  return Boolean(topic.value.trim()) && inclusion.value.some(Boolean) && exclusion.value.some(Boolean) && files.value.length > 0
})

onMounted(async () => {
  await metaStore.ensureLoaded()
})
</script>

<template>
  <div class="screening-view">
    <section class="screening-hero panel-surface">
      <div>
        <div class="eyebrow">Screening Composer</div>
        <h1>为初筛任务建立一份真正可复用的运行配置</h1>
        <p>
          这里提交的是任务，不是一次性脚本。前端会把输入文件、筛选标准和模型参数整理成稳定请求，再交给后端 API 执行。
        </p>
      </div>
      <NAlert type="info" :show-icon="false">
        当前推荐先用 DeepSeek 走通任务，再根据需要切换 Kimi。
      </NAlert>
    </section>

    <div class="screening-grid">
      <NCard title="任务基本信息" class="panel-surface">
        <NForm label-placement="top">
          <NFormItem label="任务名称">
            <NInput v-model:value="title" />
          </NFormItem>
          <NFormItem label="研究主题">
            <NInput v-model:value="topic" placeholder="例如：肥胖相关代谢调控研究" />
          </NFormItem>
        </NForm>
      </NCard>

      <NCard title="输入文件" class="panel-surface">
        <label class="dropzone">
          <input class="hidden-input" type="file" multiple @change="handleFileChange" />
          <FileUp :size="22" />
          <div class="dropzone-title">拖入或选择文献文件</div>
          <div class="dropzone-copy">
            {{ metaStore.acceptedInputFormats.join(' / ') || '.bib / .ris / .enw / .txt' }}
          </div>
        </label>

        <div class="file-list" v-if="files.length">
          <div v-for="file in files" :key="file.name" class="file-pill">
            {{ file.name }}
          </div>
        </div>
      </NCard>

      <NCard title="筛选标准" class="panel-surface card-span-2">
        <NGrid :cols="2" :x-gap="18" responsive="screen" item-responsive>
          <NGridItem span="2 m:1">
            <NForm label-placement="top">
              <NFormItem label="原始 Markdown 标准">
                <NInput v-model:value="criteriaMarkdown" type="textarea" :rows="14" placeholder="# Topic..." />
              </NFormItem>
              <NButton secondary type="primary" @click="parseCriteria">
                <template #icon>
                  <WandSparkles :size="16" />
                </template>
                解析到结构化字段
              </NButton>
            </NForm>
          </NGridItem>

          <NGridItem span="2 m:1">
            <NForm label-placement="top">
              <NFormItem label="纳入标准">
                <NDynamicInput v-model:value="inclusion" :min="1" />
              </NFormItem>
              <NFormItem label="排除标准">
                <NDynamicInput v-model:value="exclusion" :min="1" />
              </NFormItem>
            </NForm>
          </NGridItem>
        </NGrid>
      </NCard>

      <NCard title="模型与批处理" class="panel-surface card-span-2">
        <NGrid :cols="4" :x-gap="18" :y-gap="12" responsive="screen" item-responsive>
          <NGridItem span="2 m:1">
            <NFormItem label="模型提供商">
              <NSelect
                v-model:value="provider"
                :options="metaStore.providerPresets.map(item => ({ label: item.label, value: item.provider }))"
              />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="默认预设">
              <NText depth="3">{{ selectedPreset?.label || '-' }}</NText>
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="模型名称">
              <NInput v-model:value="model.model_name" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="API Key 变量">
              <NInput v-model:value="model.api_key_env" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="4">
            <NFormItem label="API Base URL">
              <NInput v-model:value="model.api_base_url" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="Batch size">
              <NInputNumber v-model:value="batchSize" :min="1" :max="50" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="目标纳入数">
              <NInputNumber v-model:value="targetIncludeCount" :min="1" :max="9999" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="最大 tokens">
              <NInputNumber v-model:value="model.max_tokens" :min="512" :max="8192" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="最小请求间隔（秒）">
              <NInputNumber v-model:value="model.min_request_interval_seconds" :min="0" :max="30" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="重试次数">
              <NInputNumber v-model:value="retryTimes" :min="0" :max="10" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="请求超时（秒）">
              <NInputNumber v-model:value="requestTimeout" :min="60" :max="600" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <NFormItem label="输入编码">
              <NInput v-model:value="encoding" />
            </NFormItem>
          </NGridItem>
          <NGridItem span="2 m:1">
            <div class="toggles">
              <NCheckbox v-model:checked="stopWhenReached">达到目标后停止</NCheckbox>
              <NCheckbox v-model:checked="allowUncertain">保留 uncertain</NCheckbox>
            </div>
          </NGridItem>
        </NGrid>
      </NCard>
    </div>

    <div class="action-bar panel-surface">
      <div>
        <div class="action-title">提交为后台任务</div>
        <div class="action-copy">提交后会跳转到任务详情页，前端会自动轮询状态并展示产物。</div>
      </div>
      <NButton :disabled="!canSubmit || tasksStore.submitting" type="primary" size="large" @click="submit">
        <template #icon>
          <CircleDashed :size="16" />
        </template>
        创建初筛任务
      </NButton>
    </div>
  </div>
</template>

<style scoped>
.screening-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.screening-hero,
.action-bar {
  padding: 24px;
}

.screening-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.card-span-2 {
  grid-column: span 2;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 12px;
  color: #6a776c;
}

h1 {
  margin: 8px 0 12px;
  font-size: 34px;
}

p {
  color: #516056;
  line-height: 1.7;
}

.dropzone {
  display: grid;
  place-items: center;
  gap: 10px;
  min-height: 200px;
  border-radius: 20px;
  border: 1px dashed #b0a38b;
  background: linear-gradient(180deg, rgba(255, 253, 248, 0.8), rgba(236, 232, 220, 0.8));
  cursor: pointer;
}

.hidden-input {
  display: none;
}

.dropzone-title {
  font-size: 18px;
  font-weight: 700;
}

.dropzone-copy {
  color: #69736a;
}

.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.file-pill {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(45, 106, 79, 0.12);
  color: #28513e;
  font-size: 13px;
}

.toggles {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 26px;
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.action-title {
  font-weight: 700;
}

.action-copy {
  color: #667368;
  margin-top: 6px;
}

@media (max-width: 1100px) {
  .screening-grid {
    grid-template-columns: 1fr;
  }

  .card-span-2 {
    grid-column: span 1;
  }

  .action-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
