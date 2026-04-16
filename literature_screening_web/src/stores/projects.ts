import { defineStore } from 'pinia'
import {
  createProject as apiCreateProject,
  createTemplate as apiCreateTemplate,
  deleteProject as apiDeleteProject,
  enrichFulltextQueue as apiEnrichFulltextQueue,
  enrichWorkbench as apiEnrichWorkbench,
  fetchProject as apiFetchProject,
  fetchProjects as apiFetchProjects,
  fetchTemplates as apiFetchTemplates,
  patchWorkbenchItem as apiPatchWorkbenchItem,
  patchWorkbenchItems as apiPatchWorkbenchItems,
  rebuildFulltextQueue as apiRebuildFulltextQueue,
  rebuildWorkbench as apiRebuildWorkbench,
  updateFulltextStatus as apiUpdateFulltextStatus,
  updateFulltextStatuses as apiUpdateFulltextStatuses,
  updateProject as apiUpdateProject,
  updateProjectWorkflow as apiUpdateProjectWorkflow
} from '@/api/client'
import type { ProjectDetail, ProjectSnapshot, ProjectWorkflowPayload, TaskTemplateRecord } from '@/types/api'

export const useProjectsStore = defineStore('projects', {
  state: (): {
    list: ProjectSnapshot[]
    currentProject: ProjectDetail | null
    templates: TaskTemplateRecord[]
    loadingList: boolean
    loadingDetail: boolean
  } => ({
    list: [],
    currentProject: null,
    templates: [],
    loadingList: false,
    loadingDetail: false
  }),
  actions: {
    async refreshProjects() {
      this.loadingList = true
      try {
        this.list = await apiFetchProjects()
      } finally {
        this.loadingList = false
      }
    },
    async loadProject(projectId: string) {
      this.loadingDetail = true
      try {
        this.currentProject = null
        this.currentProject = await apiFetchProject(projectId)
        this.templates = await apiFetchTemplates(projectId)
        return this.currentProject
      } finally {
        this.loadingDetail = false
      }
    },
    async createProject(payload: { name: string; topic: string; description: string }) {
      const project = await apiCreateProject(payload)
      await this.refreshProjects()
      return project
    },
    async updateProject(projectId: string, payload: { name: string; topic: string; description: string }) {
      const project = await apiUpdateProject(projectId, payload)
      await this.refreshProjects()
      if (this.currentProject?.id === projectId) {
        await this.loadProject(projectId)
      }
      return project
    },
    async updateProjectWorkflow(projectId: string, payload: ProjectWorkflowPayload) {
      this.currentProject = await apiUpdateProjectWorkflow(projectId, payload)
      await this.refreshProjects()
      return this.currentProject
    },
    async deleteProject(projectId: string) {
      await apiDeleteProject(projectId)
      if (this.currentProject?.id === projectId) {
        this.currentProject = null
        this.templates = []
      }
      await this.refreshProjects()
    },
    async rebuildFulltextQueue(projectId: string, sourceDatasetIds: string[]) {
      this.currentProject = await apiRebuildFulltextQueue(projectId, { source_dataset_ids: sourceDatasetIds })
      await this.refreshProjects()
      return this.currentProject
    },
    async updateFulltextStatus(
      projectId: string,
      payload: { paper_id: string; status: 'pending' | 'ready' | 'excluded' | 'unavailable' | 'deferred'; note: string }
    ) {
      this.currentProject = await apiUpdateFulltextStatus(projectId, payload)
      await this.refreshProjects()
      return this.currentProject
    },
    async updateFulltextStatuses(
      projectId: string,
      payload: { paper_ids: string[]; status: 'pending' | 'ready' | 'excluded' | 'unavailable' | 'deferred'; note?: string | null }
    ) {
      this.currentProject = await apiUpdateFulltextStatuses(projectId, payload)
      await this.refreshProjects()
      return this.currentProject
    },
    async enrichFulltextQueue(projectId: string) {
      this.currentProject = await apiEnrichFulltextQueue(projectId)
      await this.refreshProjects()
      return this.currentProject
    },
    async rebuildWorkbench(projectId: string, sourceDatasetIds: string[]) {
      this.currentProject = await apiRebuildWorkbench(projectId, { source_dataset_ids: sourceDatasetIds })
      await this.refreshProjects()
      return this.currentProject
    },
    async patchWorkbenchItem(
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
      this.currentProject = await apiPatchWorkbenchItem(projectId, candidateId, payload)
      await this.refreshProjects()
      return this.currentProject
    },
    async patchWorkbenchItems(
      projectId: string,
      payload: {
        candidate_ids: string[]
        access_status?: 'pending' | 'ready' | 'unavailable' | 'deferred' | null
        final_decision?: 'undecided' | 'include' | 'exclude' | 'deferred' | null
        access_note?: string | null
        final_note?: string | null
      }
    ) {
      this.currentProject = await apiPatchWorkbenchItems(projectId, payload)
      await this.refreshProjects()
      return this.currentProject
    },
    async enrichWorkbench(projectId: string) {
      this.currentProject = await apiEnrichWorkbench(projectId)
      await this.refreshProjects()
      return this.currentProject
    },
    async saveTemplate(payload: { name: string; payload: Record<string, unknown>; project_id?: string | null }) {
      const template = await apiCreateTemplate(payload)
      this.templates = await apiFetchTemplates(payload.project_id ?? undefined)
      return template
    }
  }
})
