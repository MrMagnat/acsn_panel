import { defineStore } from 'pinia'
import { ref } from 'vue'
import { agentsApi } from '~/api/agents'

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref([])
  const currentAgent = ref(null)
  const loading = ref(false)

  async function fetchAgents() {
    loading.value = true
    try {
      const res = await agentsApi.list()
      agents.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchAgent(id) {
    loading.value = true
    try {
      const res = await agentsApi.get(id)
      currentAgent.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function createAgent(data) {
    const res = await agentsApi.create(data)
    agents.value.push({
      id: res.data.id,
      name: res.data.name,
      is_active: res.data.is_active,
      energy_left: res.data.energy_left,
      tools_count: res.data.agent_tools?.length ?? 0,
    })
    return res.data
  }

  async function createFromTemplate(templateId) {
    const res = await agentsApi.createFromTemplate(templateId)
    agents.value.push({
      id: res.data.id,
      name: res.data.name,
      is_active: res.data.is_active,
      energy_left: res.data.energy_left,
      tools_count: res.data.agent_tools?.length ?? 0,
    })
    return res.data
  }

  async function updateAgent(id, data) {
    const res = await agentsApi.update(id, data)
    if (currentAgent.value?.id === id) {
      currentAgent.value = { ...currentAgent.value, ...res.data }
    }
    const idx = agents.value.findIndex((a) => a.id === id)
    if (idx !== -1) {
      agents.value[idx] = { ...agents.value[idx], ...res.data }
    }
    return res.data
  }

  async function deleteAgent(id) {
    await agentsApi.delete(id)
    agents.value = agents.value.filter((a) => a.id !== id)
    if (currentAgent.value?.id === id) currentAgent.value = null
  }

  return { agents, currentAgent, loading, fetchAgents, fetchAgent, createAgent, createFromTemplate, updateAgent, deleteAgent }
})
