import http from './http'

export const toolsApi = {
  // Магазин инструментов (публичный для авторизованных)
  list: () => http.get('/tools'),
  // Список активных шаблонных агентов для личного кабинета
  listTemplateAgents: () => http.get('/tools/template-agents'),
  // Запустить инструмент из магазина без агента
  runStandalone: (toolId, fieldValues) => http.post(`/tools/${toolId}/run`, { field_values: fieldValues }),
  // Вся история запусков пользователя
  getAllRunLogs: () => http.get('/run-logs'),
}
