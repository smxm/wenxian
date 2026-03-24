import { defineStore } from 'pinia'
import { createProject, deleteProject, fetchProject, fetchProjects, fetchTemplates, createTemplate, updateProject } from '@/api/client'
import type { ProjectDetail, ProjectSnapshot, TaskTemplateRecord } from '@/types/api'

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
        this.list = await fetchProjects()
      } finally {
        this.loadingList = false
      }
    },
    async loadProject(projectId: string) {
      this.loadingDetail = true
      try {
        this.currentProject = await fetchProject(projectId)
        this.templates = await fetchTemplates(projectId)
        return this.currentProject
      } finally {
        this.loadingDetail = false
      }
    },
    async createProject(payload: { name: string; topic: string; description: string }) {
      const project = await createProject(payload)
      await this.refreshProjects()
      return project
    },
    async updateProject(projectId: string, payload: { name: string; topic: string; description: string }) {
      const project = await updateProject(projectId, payload)
      await this.refreshProjects()
      if (this.currentProject?.id === projectId) {
        await this.loadProject(projectId)
      }
      return project
    },
    async deleteProject(projectId: string) {
      await deleteProject(projectId)
      if (this.currentProject?.id === projectId) {
        this.currentProject = null
        this.templates = []
      }
      await this.refreshProjects()
    },
    async saveTemplate(payload: { name: string; payload: Record<string, unknown>; project_id?: string | null }) {
      const template = await createTemplate(payload)
      this.templates = await fetchTemplates(payload.project_id ?? undefined)
      return template
    }
  }
})
