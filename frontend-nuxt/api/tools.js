import http from './http'

export const toolsApi = {
  list: () => http.get('/tools'),
  listTemplateAgents: () => http.get('/tools/template-agents'),
}
