import axios from 'axios'
import type {
  DatasetRecord,
  MetaPayload,
  ProjectDetail,
  ProjectSnapshot,
  ReportFormPayload,
  ScreeningFormPayload,
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

export async function applyReviewOverride(taskId: string, payload: { paper_id: string; decision: 'include' | 'exclude' | 'uncertain'; reason: string }) {
  const { data } = await http.post<TaskDetail>(`/tasks/${taskId}/review-overrides`, payload)
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
  formData.append('target_include_count', String(payload.target_include_count))
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

export async function updateProject(projectId: string, payload: { name: string; topic: string; description: string }) {
  const { data } = await http.put<ProjectSnapshot>(`/projects/${projectId}`, payload)
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
