import http from './http'

export const chatApi = {
  getHistory: (agentId) => http.get(`/chat/${agentId}/messages`),
  sendMessage: (agentId, content) => http.post(`/chat/${agentId}/messages`, { content }),
}
