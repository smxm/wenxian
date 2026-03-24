import { defineStore } from 'pinia'
import type { ModelSettings, ReferenceStyle } from '@/types/api'

const STORAGE_KEY = 'literature-screening-studio:drafts'

export interface ScreeningDraftState {
  projectId: string | null
  newProjectName: string
  newProjectDescription: string
  sourceDatasetIds: string[]
  parentTaskId: string | null
  selectedTemplateId: string | null
  title: string
  topic: string
  criteriaMarkdown: string
  inclusion: string[]
  exclusion: string[]
  provider: 'deepseek' | 'kimi'
  model: ModelSettings
  batchSize: number
  targetIncludeCount: number
  stopWhenReached: boolean
  allowUncertain: boolean
  retryTimes: number
  requestTimeout: number
  encoding: string
  fileNames: string[]
}

export interface ReportDraftState {
  title: string
  projectTopic: string
  reportName: string
  referenceStyle: ReferenceStyle
  retryTimes: number
  timeoutSeconds: number
}

function createDefaultScreeningDraft(): ScreeningDraftState {
  return {
    projectId: null,
    newProjectName: '',
    newProjectDescription: '',
    sourceDatasetIds: [],
    parentTaskId: null,
    selectedTemplateId: null,
    title: 'new-screening-run',
    topic: '',
    criteriaMarkdown: '',
    inclusion: [''],
    exclusion: [''],
    provider: 'deepseek',
    model: {
      provider: 'deepseek',
      model_name: 'deepseek-chat',
      api_base_url: 'https://api.deepseek.com/v1',
      api_key_env: 'DEEPSEEK_API_KEY',
      temperature: 0,
      max_tokens: 1536,
      min_request_interval_seconds: 2
    },
    batchSize: 20,
    targetIncludeCount: 30,
    stopWhenReached: true,
    allowUncertain: true,
    retryTimes: 6,
    requestTimeout: 240,
    encoding: 'auto',
    fileNames: []
  }
}

function createDefaultReportDraft(screeningTaskId?: string): ReportDraftState {
  return {
    title: screeningTaskId ? `${screeningTaskId}-report` : 'report-task',
    projectTopic: '',
    reportName: 'simple_report',
    referenceStyle: 'gbt7714',
    retryTimes: 6,
    timeoutSeconds: 240
  }
}

function readPersisted() {
  if (typeof window === 'undefined') return null
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as {
      screeningDraft?: Partial<ScreeningDraftState>
      reportDrafts?: Record<string, Partial<ReportDraftState>>
    }
  } catch {
    return null
  }
}

export const useDraftsStore = defineStore('drafts', {
  state: (): {
    hydrated: boolean
    screeningDraft: ScreeningDraftState
    screeningFiles: File[]
    reportDrafts: Record<string, ReportDraftState>
  } => ({
    hydrated: false,
    screeningDraft: createDefaultScreeningDraft(),
    screeningFiles: [],
    reportDrafts: {}
  }),
  getters: {
    hasScreeningDraft: (state) =>
      Boolean(
        state.screeningDraft.topic.trim() ||
          state.screeningDraft.criteriaMarkdown.trim() ||
          state.screeningDraft.inclusion.some(Boolean) ||
          state.screeningDraft.exclusion.some(Boolean) ||
          state.screeningFiles.length
      )
  },
  actions: {
    hydrate() {
      if (this.hydrated) return
      const persisted = readPersisted()
      if (persisted?.screeningDraft) {
        this.screeningDraft = {
          ...createDefaultScreeningDraft(),
          ...persisted.screeningDraft,
          model: {
            ...createDefaultScreeningDraft().model,
            ...(persisted.screeningDraft.model ?? {})
          },
          inclusion: persisted.screeningDraft.inclusion?.length ? persisted.screeningDraft.inclusion : [''],
          exclusion: persisted.screeningDraft.exclusion?.length ? persisted.screeningDraft.exclusion : [''],
          fileNames: persisted.screeningDraft.fileNames ?? []
        }
      }
      if (persisted?.reportDrafts) {
        this.reportDrafts = Object.fromEntries(
          Object.entries(persisted.reportDrafts).map(([taskId, draft]) => [
            taskId,
            {
              ...createDefaultReportDraft(taskId),
              ...draft
            }
          ])
        )
      }
      this.hydrated = true
    },
    persist() {
      if (typeof window === 'undefined') return
      window.localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          screeningDraft: this.screeningDraft,
          reportDrafts: this.reportDrafts
        })
      )
    },
    updateScreeningDraft(patch: Partial<ScreeningDraftState>) {
      this.screeningDraft = {
        ...this.screeningDraft,
        ...patch,
        model: {
          ...this.screeningDraft.model,
          ...(patch.model ?? {})
        }
      }
      this.persist()
    },
    setScreeningFiles(files: File[]) {
      this.screeningFiles = files
      this.screeningDraft.fileNames = files.map((file) => file.name)
      this.persist()
    },
    clearScreeningDraft() {
      this.screeningDraft = createDefaultScreeningDraft()
      this.screeningFiles = []
      this.persist()
    },
    getReportDraft(screeningTaskId: string) {
      if (!this.reportDrafts[screeningTaskId]) {
        this.reportDrafts[screeningTaskId] = createDefaultReportDraft(screeningTaskId)
      }
      return this.reportDrafts[screeningTaskId]
    },
    updateReportDraft(screeningTaskId: string, patch: Partial<ReportDraftState>) {
      const current = this.getReportDraft(screeningTaskId)
      this.reportDrafts[screeningTaskId] = {
        ...current,
        ...patch
      }
      this.persist()
    },
    clearReportDraft(screeningTaskId: string) {
      delete this.reportDrafts[screeningTaskId]
      this.persist()
    }
  }
})
