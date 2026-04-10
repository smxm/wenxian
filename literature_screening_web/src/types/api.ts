export type ProviderName = 'deepseek' | 'kimi'
export type TaskKind = 'strategy' | 'screening' | 'report'
export type TaskStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'cancelled'
export type ReferenceStyle = 'gbt7714' | 'apa7'
export type DatasetKind =
  | 'included'
  | 'excluded'
  | 'unused'
  | 'included_reviewed'
  | 'excluded_reviewed'
  | 'cumulative_included'
  | 'fulltext_ready'
  | 'report_source'
  | string
export type StrategyDatabase = 'scopus' | 'wos' | 'pubmed' | 'cnki'
export type FulltextStatus = 'pending' | 'ready' | 'excluded' | 'unavailable' | 'deferred'

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
  strategyDefaults: {
    provider: ProviderName
    model_name: string
    api_base_url: string
    api_key_env: string
    api_key?: string | null
    temperature: number
    max_tokens: number
    min_request_interval_seconds: number
    databases: Array<{ value: StrategyDatabase; label: string }>
  }
}

export interface ThreadStrategySettings {
  research_need: string
  selected_databases: StrategyDatabase[]
  model?: ModelSettings | null
  latest_task_id?: string | null
  plan?: StrategyPlan | null
}

export interface ThreadScreeningSettings {
  topic: string
  criteria_markdown: string
  inclusion: string[]
  exclusion: string[]
  model?: ModelSettings | null
  batch_size: number
  target_include_count?: number | null
  stop_when_target_reached: boolean
  allow_uncertain: boolean
  retry_times: number
  request_timeout_seconds: number
  encoding: string
}

export interface ThreadProfile {
  strategy: ThreadStrategySettings
  screening: ThreadScreeningSettings
  last_updated_at?: string | null
}

export interface ProjectSnapshot {
  id: string
  name: string
  topic: string
  description: string
  thread_profile?: ThreadProfile | null
  created_at: string
  updated_at: string
  dataset_count: number
}

export interface DatasetRecord {
  id: string
  project_id: string
  task_id?: string | null
  kind: DatasetKind
  label: string
  filename: string
  path: string
  relative_path?: string | null
  format: string
  record_count?: number | null
  source_dataset_ids: string[]
  created_at: string
  updated_at: string
  metadata: Record<string, unknown>
}

export interface FulltextQueueItem {
  paper_id: string
  title: string
  year?: number | null
  journal?: string | null
  doi?: string | null
  confidence?: number | string | null
  screening_decision?: string | null
  screening_reason?: string | null
  doi_url?: string | null
  landing_url?: string | null
  pdf_url?: string | null
  oa_status?: string | null
  status: FulltextStatus
  note: string
  updated_at: string
}

export interface TaskTemplateRecord {
  id: string
  project_id?: string | null
  name: string
  scope: 'global' | 'project'
  payload: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface TaskArtifact {
  key: string
  filename: string
  content_type: string
  size_bytes?: number | null
}

export interface TaskEvent {
  id: string
  kind: string
  message: string
  metadata: Record<string, unknown>
  created_at: string
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
  abstract?: string | null
}

export interface TaskSnapshot {
  id: string
  kind: TaskKind
  status: TaskStatus
  title: string
  phase: string
  phase_label?: string | null
  progress_current?: number | null
  progress_total?: number | null
  progress_message?: string | null
  created_at: string
  updated_at: string
  summary?: Record<string, unknown> | null
  error?: string | null
  project_id?: string | null
  parent_task_id?: string | null
  input_dataset_ids: string[]
  output_dataset_ids: string[]
  project_topic?: string | null
  model_provider?: string | null
  attempt_count: number
  artifacts: TaskArtifact[]
}

export interface TaskDetail extends TaskSnapshot {
  run_root?: string | null
  run_root_relative?: string | null
  output_dir?: string | null
  output_dir_relative?: string | null
  records: ScreeningRecordRow[]
  markdown_preview?: string | null
  events: TaskEvent[]
  strategy_plan?: StrategyPlan | null
  request_payload?: Record<string, unknown> | null
}

export interface ProjectDetail extends ProjectSnapshot {
  tasks: TaskSnapshot[]
  datasets: DatasetRecord[]
  fulltext_queue: FulltextQueueItem[]
  fulltext_source_dataset_ids: string[]
}

export interface ModelSettings {
  provider: ProviderName
  model_name: string
  api_base_url: string
  api_key_env: string
  api_key?: string
  temperature: number
  max_tokens: number
  min_request_interval_seconds: number
}

export interface ScreeningFormPayload {
  project_id?: string | null
  new_project_name?: string
  new_project_description?: string
  source_dataset_ids: string[]
  parent_task_id?: string | null
  title: string
  topic: string
  criteria_markdown?: string
  inclusion: string[]
  exclusion: string[]
  model: ModelSettings
  batch_size: number
  target_include_count?: number | null
  stop_when_target_reached: boolean
  allow_uncertain: boolean
  retry_times: number
  request_timeout_seconds: number
  encoding: string
  files: File[]
}

export interface ReportFormPayload {
  title: string
  project_id?: string | null
  screening_task_id?: string | null
  dataset_ids: string[]
  project_topic: string
  model: ModelSettings
  report_name: string
  retry_times: number
  timeout_seconds: number
  reference_style: ReferenceStyle
}

export interface StrategySearchBlock {
  database: StrategyDatabase
  title: string
  query?: string | null
  lines: string[]
  notes: string[]
}

export interface StrategyPlan {
  topic: string
  intent_summary: string
  screening_topic: string
  inclusion: string[]
  exclusion: string[]
  search_blocks: StrategySearchBlock[]
  caution_notes: string[]
}

export interface StrategyFormPayload {
  title: string
  project_id?: string | null
  new_project_name?: string
  new_project_description?: string
  project_topic?: string
  research_need: string
  selected_databases: StrategyDatabase[]
  model: ModelSettings
  retry_times: number
  timeout_seconds: number
}

export interface ProjectWorkflowPayload {
  name?: string | null
  topic?: string | null
  description?: string | null
  thread_profile: ThreadProfile
}
