import http from './http'

export const triggersApi = {
  create: (data) => http.post('/triggers', data),
  update: (id, data) => http.patch(`/triggers/${id}`, data),
  delete: (id) => http.delete(`/triggers/${id}`),
}
