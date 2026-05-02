import { defineStore } from 'pinia'
import type { ModelSettings, ProviderName, ReferenceStyle, StrategyDatabase } from '@/types/api'

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
  targetIncludeCount: number | null
  stopWhenReached: boolean
  minIncludeConfidence: number
  allowUncertain: boolean
  retryTimes: number
  requestTimeout: number
  encoding: string
  fileNames: string[]
}

export interface ReportDraftState {
  projectId: string | null
  screeningTaskId: string | null
  datasetIds: string[]
  title: string
  projectTopic: string
  reportName: string
  referenceStyle: ReferenceStyle
  sourceMode: 'original' | 'reviewed'
  retryTimes: number
  timeoutSeconds: number
  provider: ProviderName
  modelName: string
  apiBaseUrl: string
  apiKeyEnv: string
}

export interface StrategyDraftState {
  projectId: string | null
  newProjectName: string
  newProjectDescription: string
  title: string
  projectTopic: string
  researchNeed: string
  kickoffMode: 'quick' | 'plan'
  screeningTopic: string
  inclusion: string[]
  exclusion: string[]
  intentSummary: string
  selectedDatabases: StrategyDatabase[]
  timeoutSeconds: number
  retryTimes: number
}

type ApiKeyMap = Partial<Record<ProviderName, string>>

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
      max_tokens: 4096,
      min_request_interval_seconds: 2
    },
    batchSize: 10,
    targetIncludeCount: null,
    stopWhenReached: false,
    minIncludeConfidence: 0.8,
    allowUncertain: true,
    retryTimes: 6,
    requestTimeout: 240,
    encoding: 'auto',
    fileNames: []
  }
}

function createDefaultStrategyDraft(): StrategyDraftState {
  return {
    projectId: null,
    newProjectName: '',
    newProjectDescription: '',
    title: 'new-search-strategy',
    projectTopic: '',
    researchNeed: '',
    kickoffMode: 'quick',
    screeningTopic: '',
    inclusion: [''],
    exclusion: [''],
    intentSummary: '',
    selectedDatabases: ['scopus', 'wos', 'pubmed', 'cnki'],
    timeoutSeconds: 180,
    retryTimes: 4
  }
}

function createDefaultReportDraft(): ReportDraftState {
  return {
    projectId: null,
    screeningTaskId: null,
    datasetIds: [],
    title: 'report-task',
    projectTopic: '',
    reportName: 'simple_report',
    referenceStyle: 'gbt7714',
    sourceMode: 'original',
    retryTimes: 6,
    timeoutSeconds: 240,
    provider: 'deepseek',
    modelName: 'deepseek-reasoner',
    apiBaseUrl: 'https://api.deepseek.com/v1',
    apiKeyEnv: 'DEEPSEEK_API_KEY'
  }
}

function readPersisted() {
  if (typeof window === 'undefined') return null
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as {
      screeningDraft?: Partial<ScreeningDraftState>
      strategyDraft?: Partial<StrategyDraftState>
      reportDrafts?: Record<string, Partial<ReportDraftState>>
      apiKeys?: ApiKeyMap
    }
  } catch {
    return null
  }
}

export const useDraftsStore = defineStore('drafts', {
  state: (): {
    hydrated: boolean
    screeningDraft: ScreeningDraftState
    strategyDraft: StrategyDraftState
    screeningFiles: File[]
    reportDrafts: Record<string, ReportDraftState>
    apiKeys: ApiKeyMap
  } => ({
    hydrated: false,
    screeningDraft: createDefaultScreeningDraft(),
    strategyDraft: createDefaultStrategyDraft(),
    screeningFiles: [],
    reportDrafts: {},
    apiKeys: {}
  }),
  getters: {
    hasScreeningDraft: (state) =>
      Boolean(
        state.screeningDraft.topic.trim() ||
          state.screeningDraft.criteriaMarkdown.trim() ||
          state.screeningDraft.inclusion.some(Boolean) ||
          state.screeningDraft.exclusion.some(Boolean) ||
          state.screeningFiles.length
      ),
    hasStrategyDraft: (state) =>
      Boolean(
        state.strategyDraft.newProjectName.trim() ||
          state.strategyDraft.newProjectDescription.trim() ||
          state.strategyDraft.researchNeed.trim() ||
          state.strategyDraft.screeningTopic.trim() ||
          state.strategyDraft.intentSummary.trim() ||
          state.strategyDraft.inclusion.some(Boolean) ||
          state.strategyDraft.exclusion.some(Boolean) ||
          state.strategyDraft.kickoffMode !== createDefaultStrategyDraft().kickoffMode ||
          state.strategyDraft.retryTimes !== createDefaultStrategyDraft().retryTimes ||
          state.strategyDraft.timeoutSeconds !== createDefaultStrategyDraft().timeoutSeconds ||
          state.strategyDraft.selectedDatabases.join('|') !== createDefaultStrategyDraft().selectedDatabases.join('|')
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
      if (persisted?.strategyDraft) {
        this.strategyDraft = {
          ...createDefaultStrategyDraft(),
          ...persisted.strategyDraft,
          inclusion: persisted.strategyDraft.inclusion?.length ? persisted.strategyDraft.inclusion : [''],
          exclusion: persisted.strategyDraft.exclusion?.length ? persisted.strategyDraft.exclusion : [''],
          selectedDatabases: persisted.strategyDraft.selectedDatabases?.length
            ? persisted.strategyDraft.selectedDatabases
            : createDefaultStrategyDraft().selectedDatabases
        }
      }
      if (persisted?.reportDrafts) {
        this.reportDrafts = Object.fromEntries(
          Object.entries(persisted.reportDrafts).map(([taskId, draft]) => [
            taskId,
            {
              ...createDefaultReportDraft(),
              ...draft
            }
          ])
        )
      }
      if (persisted && 'apiKeys' in persisted && persisted.apiKeys) {
        this.apiKeys = persisted.apiKeys as ApiKeyMap
        if (this.screeningDraft.provider && this.apiKeys[this.screeningDraft.provider]) {
          this.screeningDraft.model.api_key = this.apiKeys[this.screeningDraft.provider]
        }
      }
      this.hydrated = true
    },
    persist() {
      if (typeof window === 'undefined') return
      window.localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          screeningDraft: this.screeningDraft,
          strategyDraft: this.strategyDraft,
          reportDrafts: this.reportDrafts,
          apiKeys: this.apiKeys
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
      if (this.screeningDraft.model.api_key) {
        this.apiKeys[this.screeningDraft.provider] = this.screeningDraft.model.api_key
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
    updateStrategyDraft(patch: Partial<StrategyDraftState>) {
      this.strategyDraft = {
        ...this.strategyDraft,
        ...patch,
        inclusion: patch.inclusion ?? this.strategyDraft.inclusion,
        exclusion: patch.exclusion ?? this.strategyDraft.exclusion,
        selectedDatabases: patch.selectedDatabases ?? this.strategyDraft.selectedDatabases
      }
      this.persist()
    },
    clearStrategyDraft() {
      this.strategyDraft = createDefaultStrategyDraft()
      this.persist()
    },
    getReportDraft(draftKey: string) {
      if (!this.reportDrafts[draftKey]) {
        this.reportDrafts[draftKey] = createDefaultReportDraft()
      }
      return this.reportDrafts[draftKey]
    },
    updateReportDraft(draftKey: string, patch: Partial<ReportDraftState>) {
      const current = this.getReportDraft(draftKey)
      this.reportDrafts[draftKey] = {
        ...current,
        ...patch
      }
      this.persist()
    },
    clearReportDraft(draftKey: string) {
      delete this.reportDrafts[draftKey]
      this.persist()
    },
    setProviderApiKey(provider: ProviderName, apiKey: string) {
      if (apiKey) this.apiKeys[provider] = apiKey
      else delete this.apiKeys[provider]
      if (this.screeningDraft.provider === provider) {
        this.screeningDraft.model.api_key = apiKey
      }
      this.persist()
    },
    getProviderApiKey(provider: ProviderName) {
      return this.apiKeys[provider] ?? ''
    }
  }
})
