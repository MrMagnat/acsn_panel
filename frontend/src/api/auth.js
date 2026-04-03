import http from './http'

export const authApi = {
  register: (data) => http.post('/auth/register', data),
  login: (data) => http.post('/auth/login', data),
  // ASCN SSO
  ascnLogin: (email, password) => http.post('/auth/ascn-login', { email, password }),
  ascnToken: (token) => http.post('/auth/ascn-token', { token }),
  refresh: (refresh_token) => http.post('/auth/refresh', { refresh_token }),
  me: () => http.get('/auth/me'),
}
