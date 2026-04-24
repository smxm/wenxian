import axios from 'axios'
import type {
  DatasetRecord,
  MetaPayload,
  ProjectDetail,
  ProjectSnapshot,
  ThreadPrefillPayload,
  ThreadPrefillResponse,
  ProjectWorkflowPayload,
  ReportFormPayload,
  ScreeningFormPayload,
  StrategyFormPayload,
  TaskDetail,
  TaskSnapshot,
  TaskTemplateRecord
} from '@/types/api'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export async function fetchMeta() {
  const { data } = await http.get<MetaPayload>('/meta')
  return data
}

export async function fetchTasks() {
  const { data } = await http.get<TaskSnapshot[]>('/tasks')
  return data
}

export async function fetchProjectTasks(projectId: string) {
  const { data } = await http.get<TaskSnapshot[]>('/tasks', { params: { project_id: projectId } })
  return data
}

export async function fetchTask(taskId: string) {
  const { data } = await http.get<TaskDetail>(`/tasks/${taskId}`)
  return data
}

export async function retryTask(taskId: string, mode: 'retry' | 'resume' = 'resume') {
  const { data } = await http.post<TaskSnapshot>(`/tasks/${taskId}/retry`, { mode })
  return data
}

export async function cancelTask(taskId: string) {
  const { data } = await http.post<TaskSnapshot>(`/tasks/${taskId}/cancel`)
  return data
}

export async function deleteTask(taskId: string) {
  const { data } = await http.delete<{ status: string; task_id: string; project_id?: string | null }>(`/tasks/${taskId}`)
  return data
}

export async function applyReviewOverride(taskId: string, payload: { paper_id: string; decision: 'include' | 'exclude' | 'uncertain'; reason: string }) {
  const { data } = await http.post<TaskDetail>(`/tasks/${taskId}/review-overrides`, payload)
  return data
}

export async function applyBulkReviewOverride(
  taskId: string,
  payload: { entries_text: string; decision: 'include' | 'exclude' | 'uncertain'; reason: string }
) {
  const { data } = await http.post<TaskDetail>(`/tasks/${taskId}/review-overrides/bulk`, payload)
  return data
}

export async function applySelectionReviewOverride(
  taskId: string,
  payload: { paper_ids: string[]; decision: 'include' | 'exclude' | 'uncertain'; reason: string }
) {
  const { data } = await http.post<TaskDetail>(`/tasks/${taskId}/review-overrides/selection`, payload)
  return data
}

export async function applyReferenceOverride(taskId: string, payload: { references_text: string }) {
  const { data } = await http.post<TaskDetail>(`/tasks/${taskId}/reference-overrides`, payload)
  return data
}

export async function createScreeningTask(payload: ScreeningFormPayload) {
  const formData = new FormData()
  if (payload.project_id) formData.append('project_id', payload.project_id)
  if (payload.new_project_name) formData.append('new_project_name', payload.new_project_name)
  if (payload.new_project_description) formData.append('new_project_description', payload.new_project_description)
  if (payload.parent_task_id) formData.append('parent_task_id', payload.parent_task_id)
  formData.append('title', payload.title)
  formData.append('topic', payload.topic)
  if (payload.criteria_markdown) formData.append('criteria_markdown', payload.criteria_markdown)
  formData.append('inclusion_json', JSON.stringify(payload.inclusion))
  formData.append('exclusion_json', JSON.stringify(payload.exclusion))
  formData.append('source_dataset_ids_json', JSON.stringify(payload.source_dataset_ids))
  formData.append('provider', payload.model.provider)
  formData.append('model_name', payload.model.model_name)
  formData.append('api_base_url', payload.model.api_base_url)
  formData.append('api_key_env', payload.model.api_key_env)
  if (payload.model.api_key) formData.append('api_key', payload.model.api_key)
  formData.append('temperature', String(payload.model.temperature))
  formData.append('max_tokens', String(payload.model.max_tokens))
  formData.append('min_request_interval_seconds', String(payload.model.min_request_interval_seconds))
  formData.append('batch_size', String(payload.batch_size))
  if (payload.target_include_count !== null && payload.target_include_count !== undefined) {
    formData.append('target_include_count', String(payload.target_include_count))
  }
  formData.append('stop_when_target_reached', String(payload.stop_when_target_reached))
  formData.append('allow_uncertain', String(payload.allow_uncertain))
  formData.append('retry_times', String(payload.retry_times))
  formData.append('request_timeout_seconds', String(payload.request_timeout_seconds))
  formData.append('encoding', payload.encoding)
  for (const file of payload.files) {
    formData.append('files', file)
  }
  const { data } = await http.post<TaskSnapshot>('/screening/tasks', formData)
  return data
}

export async function createReportTask(payload: ReportFormPayload) {
  const { data } = await http.post<TaskSnapshot>('/report/tasks', payload)
  return data
}

export async function createStrategyTask(payload: StrategyFormPayload) {
  const { data } = await http.post<TaskSnapshot>('/strategy/tasks', payload)
  return data
}

export async function prefillThreadSetup(payload: ThreadPrefillPayload) {
  const { data } = await http.post<ThreadPrefillResponse>('/threads/prefill', payload)
  return data
}

export async function fetchProjects() {
  const { data } = await http.get<ProjectSnapshot[]>('/projects')
  return data
}

export async function fetchProject(projectId: string) {
  const { data } = await http.get<ProjectDetail>(`/projects/${projectId}`)
  return data
}

export async function createProject(payload: { name: string; topic: string; description: string }) {
  const { data } = await http.post<ProjectSnapshot>('/projects', payload)
  return data
}

export async function rebuildFulltextQueue(projectId: string, payload: { source_dataset_ids: string[] }) {
  const { data } = await http.post<ProjectDetail>(`/projects/${projectId}/fulltext/rebuild`, payload)
  return data
}

export async function updateFulltextStatus(
  projectId: string,
  payload: { paper_id: string; status: 'pending' | 'ready' | 'excluded' | 'unavailable' | 'deferred'; note: string }
) {
  const { data } = await http.post<ProjectDetail>(`/projects/${projectId}/fulltext/status`, payload)
  return data
}

export async function updateFulltextStatuses(
  projectId: string,
  payload: { paper_ids: string[]; status: 'pending' | 'ready' | 'excluded' | 'unavailable' | 'deferred'; note?: string | null }
) {
  const { data } = await http.post<ProjectDetail>(`/projects/${projectId}/fulltext/status/batch`, payload)
  return data
}

export async function enrichFulltextQueue(projectId: string) {
  const { data } = await http.post<ProjectDetail>(`/projects/${projectId}/fulltext/enrich`)
  return data
}

export async function rebuildWorkbench(projectId: string, payload: { source_dataset_ids: string[] }) {
  const { data } = await http.post<ProjectDetail>(`/projects/${projectId}/workbench/rebuild`, payload)
  return data
}

export async function patchWorkbenchItem(
  projectId: string,
  candidateId: string,
  payload: {
    access_status?: 'pending' | 'ready' | 'unavailable' | 'deferred' | null
    final_decision?: 'undecided' | 'include' | 'exclude' | 'deferred' | null
    access_note?: string | null
    final_note?: string | null
    preferred_open_url?: string | null
    preferred_pdf_url?: string | null
  }
) {
  const { data } = await http.post<ProjectDetail>(`/projects/${projectId}/workbench/items/${candidateId}`, payload)
  return data
}

export async function patchWorkbenchItems(
  projectId: string,
  payload: {
    candidate_ids: string[]
    access_status?: 'pending' | 'ready' | 'unavailable' | 'deferred' | null
    final_decision?: 'undecided' | 'include' | 'exclude' | 'deferred' | null
    access_note?: string | null
    final_note?: string | null
  }
) {
  const { data } = await http.post<ProjectDetail>(`/projects/${projectId}/workbench/items/batch`, payload)
  return data
}

export async function enrichWorkbench(projectId: string) {
  const { data } = await http.post<ProjectDetail>(`/projects/${projectId}/workbench/enrich`)
  return data
}

export async function updateProject(projectId: string, payload: { name: string; topic: string; description: string }) {
  const { data } = await http.put<ProjectSnapshot>(`/projects/${projectId}`, payload)
  return data
}

export async function updateProjectWorkflow(projectId: string, payload: ProjectWorkflowPayload) {
  const { data } = await http.put<ProjectDetail>(`/projects/${projectId}/workflow`, payload)
  return data
}

export async function deleteProject(projectId: string) {
  const { data } = await http.delete<{ status: string }>(`/projects/${projectId}`)
  return data
}

export async function fetchDataset(datasetId: string) {
  const { data } = await http.get<DatasetRecord>(`/datasets/${datasetId}`)
  return data
}

export async function fetchTemplates(projectId?: string) {
  const { data } = await http.get<TaskTemplateRecord[]>('/templates', { params: projectId ? { project_id: projectId } : undefined })
  return data
}

export async function createTemplate(payload: { name: string; payload: Record<string, unknown>; project_id?: string | null }) {
  const form = new FormData()
  form.append('name', payload.name)
  form.append('payload_json', JSON.stringify(payload.payload))
  if (payload.project_id) form.append('project_id', payload.project_id)
  const { data } = await http.post<TaskTemplateRecord>('/templates', form)
  return data
}

export function getArtifactUrl(taskId: string, artifactKey: string) {
  return `/api/tasks/${taskId}/artifacts/${artifactKey}`
}
