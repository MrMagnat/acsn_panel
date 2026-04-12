import http from './http'

export const partnerApi = {
  getStats: () => http.get('/partner/me'),
  getTools: () => http.get('/partner/tools'),
  getTransactions: () => http.get('/partner/transactions'),
  requestWithdraw: (data) => http.post('/partner/withdraw', data),
}
