import { defineStore } from 'pinia'
import { fetchMeta } from '@/api/client'
import type { MetaPayload } from '@/types/api'

export const useMetaStore = defineStore('meta', {
  state: (): { data: MetaPayload | null; loading: boolean } => ({
    data: null,
    loading: false
  }),
  getters: {
    providerPresets: (state) => state.data?.providers ?? [],
    referenceStyles: (state) => state.data?.referenceStyles ?? [],
    acceptedInputFormats: (state) => state.data?.acceptedInputFormats ?? []
  },
  actions: {
    async ensureLoaded() {
      if (this.data || this.loading) return
      this.loading = true
      try {
        this.data = await fetchMeta()
      } finally {
        this.loading = false
      }
    }
  }
})
