import http from './http'

export const kbApi = {
  list: () => http.get('/kb'),
  create: (name) => http.post('/kb', { name }),
  get: (id) => http.get(`/kb/${id}`),
  rename: (id, name) => http.patch(`/kb/${id}`, { name }),
  delete: (id) => http.delete(`/kb/${id}`),

  addField: (id, name, field_type = 'text') => http.post(`/kb/${id}/fields`, { name, field_type }),
  updateField: (id, fieldId, data) => http.patch(`/kb/${id}/fields/${fieldId}`, data),
  deleteField: (id, fieldId) => http.delete(`/kb/${id}/fields/${fieldId}`),

  addRecord: (id, data = {}) => http.post(`/kb/${id}/records`, { data }),
  updateRecord: (id, recordId, data) => http.patch(`/kb/${id}/records/${recordId}`, { data }),
  deleteRecord: (id, recordId) => http.delete(`/kb/${id}/records/${recordId}`),

  importCsv: (id, file) => {
    const form = new FormData()
    form.append('file', file)
    return http.post(`/kb/${id}/import`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  exportCsv: (id) => http.get(`/kb/${id}/export`, { responseType: 'blob' }),
}
