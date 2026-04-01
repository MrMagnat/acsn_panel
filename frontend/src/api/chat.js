import http from './http'

export const chatApi = {
  getHistory: (agentId) => http.get(`/chat/${agentId}/messages`),
  sendMessage: (agentId, content, llm_model, llm_token) =>
    http.post(`/chat/${agentId}/messages`, { content, llm_model, llm_token }),
}
