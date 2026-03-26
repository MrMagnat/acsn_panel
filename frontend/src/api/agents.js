import http from './http'

export const agentsApi = {
  list: () => http.get('/agents'),
  get: (id) => http.get(`/agents/${id}`),
  create: (data) => http.post('/agents', data),
  createFromTemplate: (templateId) => http.post(`/agents/from-template/${templateId}`),
  update: (id, data) => http.patch(`/agents/${id}`, data),
  delete: (id) => http.delete(`/agents/${id}`),

  addTool: (agentId, toolId) => http.post(`/agents/${agentId}/tools`, { tool_id: toolId }),
  removeTool: (agentId, toolId) => http.delete(`/agents/${agentId}/tools/${toolId}`),
  updateToolFields: (agentId, toolId, fieldValues) =>
    http.patch(`/agents/${agentId}/tools/${toolId}`, { field_values: fieldValues }),
  runTool: (agentId, toolId) =>
    http.post(`/agents/${agentId}/tools/${toolId}/run`),

  getRunLogs: (agentId) => http.get(`/agents/${agentId}/run-logs`),
  pollRunLog: (logId) => http.get(`/run-logs/${logId}`),
  cancelRunLog: (logId) => http.post(`/run-logs/${logId}/cancel`),
}
