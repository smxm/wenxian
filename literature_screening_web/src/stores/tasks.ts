import { defineStore } from 'pinia'
import { applyReviewOverride, createReportTask, createScreeningTask, fetchTask, fetchTasks, retryTask } from '@/api/client'
import type { ReportFormPayload, ScreeningFormPayload, TaskDetail, TaskSnapshot } from '@/types/api'

export const useTasksStore = defineStore('tasks', {
  state: (): {
    list: TaskSnapshot[]
    currentTask: TaskDetail | null
    loadingList: boolean
    loadingTask: boolean
    submitting: boolean
    pollTimer: number | null
  } => ({
    list: [],
    currentTask: null,
    loadingList: false,
    loadingTask: false,
    submitting: false,
    pollTimer: null
  }),
  getters: {
    latestScreeningTask: (state) => state.list.find(task => task.kind === 'screening'),
    runningTasks: (state) => state.list.filter(task => task.status === 'running' || task.status === 'pending'),
    completedReports: (state) => state.list.filter(task => task.kind === 'report' && task.status === 'succeeded')
  },
  actions: {
    async refreshList() {
      if (this.loadingList) return
      this.loadingList = true
      try {
        this.list = await fetchTasks()
        if (this.currentTask && this.runningTasks.some(task => task.id === this.currentTask?.id)) {
          await this.loadTask(this.currentTask.id, true)
        }
        if (this.runningTasks.length) this.startPolling()
        else this.stopPolling()
      } finally {
        this.loadingList = false
      }
    },
    async loadTask(taskId: string, silent = false) {
      if (!silent) this.loadingTask = true
      try {
        this.currentTask = await fetchTask(taskId)
        if (this.currentTask.status === 'running' || this.currentTask.status === 'pending') {
          this.startPolling()
        }
        return this.currentTask
      } finally {
        if (!silent) this.loadingTask = false
      }
    },
    startPolling() {
      if (typeof window === 'undefined' || this.pollTimer !== null) return
      this.pollTimer = window.setInterval(() => {
        void this.refreshList()
      }, 4000)
    },
    stopPolling() {
      if (this.pollTimer !== null && typeof window !== 'undefined') {
        window.clearInterval(this.pollTimer)
      }
      this.pollTimer = null
    },
    async submitScreening(payload: ScreeningFormPayload) {
      this.submitting = true
      try {
        const task = await createScreeningTask(payload)
        await this.refreshList()
        this.startPolling()
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
        this.startPolling()
        return task
      } finally {
        this.submitting = false
      }
    },
    async retry(taskId: string, mode: 'retry' | 'resume' = 'resume') {
      this.submitting = true
      try {
        const task = await retryTask(taskId, mode)
        await this.refreshList()
        await this.loadTask(task.id, true)
        this.startPolling()
        return task
      } finally {
        this.submitting = false
      }
    },
    async review(taskId: string, payload: { paper_id: string; decision: 'include' | 'exclude' | 'uncertain'; reason: string }) {
      this.submitting = true
      try {
        this.currentTask = await applyReviewOverride(taskId, payload)
        await this.refreshList()
        return this.currentTask
      } finally {
        this.submitting = false
      }
    }
  }
})
