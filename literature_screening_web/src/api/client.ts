import axios from 'axios'
import type { MetaPayload, ReportFormPayload, ScreeningFormPayload, TaskDetail, TaskSnapshot } from '@/types/api'

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

export async function fetchTask(taskId: string) {
  const { data } = await http.get<TaskDetail>(`/tasks/${taskId}`)
  return data
}

export async function createScreeningTask(payload: ScreeningFormPayload) {
  const formData = new FormData()
  formData.append('title', payload.title)
  formData.append('topic', payload.topic)
  formData.append('inclusion_json', JSON.stringify(payload.inclusion))
  formData.append('exclusion_json', JSON.stringify(payload.exclusion))
  formData.append('provider', payload.model.provider)
  formData.append('model_name', payload.model.model_name)
  formData.append('api_base_url', payload.model.api_base_url)
  formData.append('api_key_env', payload.model.api_key_env)
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

export function getArtifactUrl(taskId: string, artifactKey: string) {
  return `/api/tasks/${taskId}/artifacts/${artifactKey}`
}
