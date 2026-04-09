import http from './http'

export const subscriptionApi = {
  get: () => http.get('/subscription'),
  plans: () => http.get('/subscription/plans'),
}
