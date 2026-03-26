import http from './http'

export const authApi = {
  register: (data) => http.post('/auth/register', data),
  login: (data) => http.post('/auth/login', data),
  refresh: (refresh_token) => http.post('/auth/refresh', { refresh_token }),
  me: () => http.get('/auth/me'),
}
