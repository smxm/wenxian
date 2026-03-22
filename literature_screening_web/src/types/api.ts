export type ProviderName = 'deepseek' | 'kimi'
export type TaskKind = 'screening' | 'report'
export type TaskStatus = 'pending' | 'running' | 'succeeded' | 'failed'
export type ReferenceStyle = 'gbt7714' | 'apa7'

export interface ProviderPreset {
  provider: ProviderName
  label: string
  defaultModel: string
  defaultBaseUrl: string
  defaultApiKeyEnv: string
}

export interface MetaPayload {
  providers: ProviderPreset[]
  referenceStyles: Array<{ value: ReferenceStyle; label: string }>
  acceptedInputFormats: string[]
}

export interface TaskArtifact {
  key: string
  filename: string
  content_type: string
  size_bytes?: number | null
}

export interface ScreeningRecordRow {
  paper_id: string
  title: string
  decision: string
  confidence?: number | string | null
  reason: string
  year?: number | null
  journal?: string | null
  doi?: string | null
}

export interface TaskSnapshot {
  id: string
  kind: TaskKind
  status: TaskStatus
  title: string
  phase: string
  created_at: string
  updated_at: string
  summary?: Record<string, unknown> | null
  error?: string | null
  project_topic?: string | null
  model_provider?: string | null
  artifacts: TaskArtifact[]
}

export interface TaskDetail extends TaskSnapshot {
  run_root?: string | null
  output_dir?: string | null
  records: ScreeningRecordRow[]
  markdown_preview?: string | null
}

export interface ModelSettings {
  provider: ProviderName
  model_name: string
  api_base_url: string
  api_key_env: string
  temperature: number
  max_tokens: number
  min_request_interval_seconds: number
}

export interface ScreeningFormPayload {
  title: string
  topic: string
  inclusion: string[]
  exclusion: string[]
  model: ModelSettings
  batch_size: number
  target_include_count: number
  stop_when_target_reached: boolean
  allow_uncertain: boolean
  retry_times: number
  request_timeout_seconds: number
  encoding: string
  files: File[]
}

export interface ReportFormPayload {
  title: string
  screening_task_id: string
  project_topic: string
  model: ModelSettings
  report_name: string
  retry_times: number
  timeout_seconds: number
  reference_style: ReferenceStyle
}
