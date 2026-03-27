import { defineStore } from 'pinia'
import { ref } from 'vue'
import { toolsApi } from '~/api/tools'

export const useToolsStore = defineStore('tools', () => {
  const tools = ref([])
  const loading = ref(false)

  async function fetchTools() {
    loading.value = true
    try {
      const res = await toolsApi.list()
      tools.value = res.data
    } finally {
      loading.value = false
    }
  }

  return { tools, loading, fetchTools }
})
