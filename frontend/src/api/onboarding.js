import http from './http'

export const onboardingApi = {
  getConfig: () => http.get('/onboarding'),
  adminGetConfig: () => http.get('/admin/onboarding'),
  adminSaveConfig: (config) => http.put('/admin/onboarding', config),
}
