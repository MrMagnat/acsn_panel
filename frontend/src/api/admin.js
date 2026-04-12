import http from './http'

export const adminApi = {
  // Пользователи
  getUsers: (params) => http.get('/admin/users', { params }),
  updateUser: (id, data) => http.patch(`/admin/users/${id}`, data),
  deleteUser: (id) => http.delete(`/admin/users/${id}`),

  // Шаблонные агенты
  getTemplates: () => http.get('/admin/template-agents'),
  getTemplate: (id) => http.get(`/admin/template-agents/${id}`),
  createTemplate: (data) => http.post('/admin/template-agents', data),
  updateTemplate: (id, data) => http.patch(`/admin/template-agents/${id}`, data),
  deleteTemplate: (id) => http.delete(`/admin/template-agents/${id}`),

  // Энергия пользователей
  getUserEnergy: (userId) => http.get(`/admin/users/${userId}/energy`),
  adjustUserEnergy: (userId, data) => http.post(`/admin/users/${userId}/energy`, data),
  adjustUserBalance: (userId, data) => http.post(`/admin/users/${userId}/balance-usd`, data),

  // Тарифные планы платформы
  getTariffPlans: () => http.get('/admin/tariff-plans'),
  createTariffPlan: (data) => http.post('/admin/tariff-plans', data),
  updateTariffPlan: (id, data) => http.put(`/admin/tariff-plans/${id}`, data),
  deleteTariffPlan: (id) => http.delete(`/admin/tariff-plans/${id}`),
  setUserTariff: (userId, data) => http.post(`/admin/users/${userId}/set-tariff`, data),
  adjustUserTokens: (userId, data) => http.post(`/admin/users/${userId}/tokens`, data),

  // Скиллы
  getSkills: () => http.get('/admin/skills'),
  createSkill: (data) => http.post('/admin/skills', data),
  updateSkill: (id, data) => http.put(`/admin/skills/${id}`, data),
  deleteSkill: (id) => http.delete(`/admin/skills/${id}`),

  // ASCN маппинг
  getAscnSlugs: () => http.get('/admin/ascn-slugs'),
  getTariffMappings: () => http.get('/admin/tariff-mappings'),
  saveTariffMappings: (data) => http.put('/admin/tariff-mappings', data),

  // Инструменты
  getTools: () => http.get('/admin/tools'),
  getTool: (id) => http.get(`/admin/tools/${id}`),
  createTool: (data) => http.post('/admin/tools', data),
  updateTool: (id, data) => http.patch(`/admin/tools/${id}`, data),
  deleteTool: (id) => http.delete(`/admin/tools/${id}`),

  // Партнёрская программа
  getPartners: () => http.get('/admin/partner'),
  adjustPartnerTokens: (userId, data) => http.post(`/admin/partner/${userId}/adjust`, data),
  getPartnerTransactions: (userId) => http.get(`/admin/partner/${userId}/transactions`),
  getPartnerSettings: () => http.get('/admin/partner/settings'),
  savePartnerSettings: (data) => http.put('/admin/partner/settings', data),
  getWithdrawRequests: () => http.get('/admin/partner/withdrawals'),
  updateWithdrawRequest: (id, data) => http.patch(`/admin/partner/withdrawals/${id}`, data),
}
