import http from './http'

export const skillsApi = {
  // Каталог
  list: () => http.get('/skills'),

  // Добавить/убрать скилл у агента
  addToAgent: (agentId, skillId) => http.post(`/agents/${agentId}/skills/${skillId}`),
  removeFromAgent: (agentId, skillId) => http.delete(`/agents/${agentId}/skills/${skillId}`),
}
