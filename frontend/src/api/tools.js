import http from './http'

export const toolsApi = {
  // Магазин инструментов (публичный для авторизованных)
  list: () => http.get('/tools'),
  // Список активных шаблонных агентов для личного кабинета
  listTemplateAgents: () => http.get('/tools/template-agents'),
}
