import { defineStore } from 'pinia'
import { createReportTask, createScreeningTask, fetchTask, fetchTasks } from '@/api/client'
import type { ReportFormPayload, ScreeningFormPayload, TaskDetail, TaskSnapshot } from '@/types/api'

export const useTasksStore = defineStore('tasks', {
  state: (): {
    list: TaskSnapshot[]
    currentTask: TaskDetail | null
    loadingList: boolean
    loadingTask: boolean
    submitting: boolean
  } => ({
    list: [],
    currentTask: null,
    loadingList: false,
    loadingTask: false,
    submitting: false
  }),
  getters: {
    latestScreeningTask: (state) => state.list.find(task => task.kind === 'screening'),
    runningTasks: (state) => state.list.filter(task => task.status === 'running'),
    completedReports: (state) => state.list.filter(task => task.kind === 'report' && task.status === 'succeeded')
  },
  actions: {
    async refreshList() {
      this.loadingList = true
      try {
        this.list = await fetchTasks()
      } finally {
        this.loadingList = false
      }
    },
    async loadTask(taskId: string) {
      this.loadingTask = true
      try {
        this.currentTask = await fetchTask(taskId)
        return this.currentTask
      } finally {
        this.loadingTask = false
      }
    },
    async submitScreening(payload: ScreeningFormPayload) {
      this.submitting = true
      try {
        const task = await createScreeningTask(payload)
        await this.refreshList()
        return task
      } finally {
        this.submitting = false
      }
    },
    async submitReport(payload: ReportFormPayload) {
      this.submitting = true
      try {
        const task = await createReportTask(payload)
        await this.refreshList()
        return task
      } finally {
        this.submitting = false
      }
    }
  }
})
