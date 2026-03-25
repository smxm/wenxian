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
    acceptedInputFormats: (state) => state.data?.acceptedInputFormats ?? [],
    strategyDefaults: (state) =>
      state.data?.strategyDefaults ?? {
        provider: 'deepseek',
        model_name: 'deepseek-reasoner',
        api_base_url: 'https://api.deepseek.com/v1',
        api_key_env: 'DEEPSEEK_API_KEY',
        temperature: 0,
        max_tokens: 4096,
        min_request_interval_seconds: 2,
        databases: [
          { value: 'scopus', label: 'Scopus 高级检索' },
          { value: 'wos', label: 'Web of Science 高级检索' },
          { value: 'pubmed', label: 'PubMed 高级检索' },
          { value: 'cnki', label: '知网高级检索（篇关摘）' }
        ]
      }
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
