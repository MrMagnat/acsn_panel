import http from './http'

export const adminApi = {
  // Пользователи
  getUsers: (params) => http.get('/admin/users', { params }),
  updateUser: (id, data) => http.patch(`/admin/users/${id}`, data),

  // Шаблонные агенты
  getTemplates: () => http.get('/admin/template-agents'),
  getTemplate: (id) => http.get(`/admin/template-agents/${id}`),
  createTemplate: (data) => http.post('/admin/template-agents', data),
  updateTemplate: (id, data) => http.patch(`/admin/template-agents/${id}`, data),
  deleteTemplate: (id) => http.delete(`/admin/template-agents/${id}`),

  // Энергия пользователей
  getUserEnergy: (userId) => http.get(`/admin/users/${userId}/energy`),
  adjustUserEnergy: (userId, data) => http.post(`/admin/users/${userId}/energy`, data),

  // Инструменты
  getTools: () => http.get('/admin/tools'),
  getTool: (id) => http.get(`/admin/tools/${id}`),
  createTool: (data) => http.post('/admin/tools', data),
  updateTool: (id, data) => http.patch(`/admin/tools/${id}`, data),
  deleteTool: (id) => http.delete(`/admin/tools/${id}`),
}
