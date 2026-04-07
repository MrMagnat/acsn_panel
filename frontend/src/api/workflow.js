import http from './http'

export const workflowApi = {
  list: (agentId) => http.get('/workflows', { params: { agent_id: agentId } }),
  create: (data) => http.post('/workflows', data),
  get: (id) => http.get(`/workflows/${id}`),
  update: (id, data) => http.patch(`/workflows/${id}`, data),
  delete: (id) => http.delete(`/workflows/${id}`),
  run: (id) => http.post(`/workflows/${id}/run`),
  runs: (id) => http.get(`/workflows/${id}/runs`),
  runningStatus: (id) => http.get(`/workflows/${id}/running-status`),
  stop: (id) => http.post(`/workflows/${id}/stop`),
}
