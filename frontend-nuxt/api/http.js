import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  if (import.meta.client) {
    const token = localStorage.getItem('access_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const { useAuthStore } = await import('~/stores/auth')
      const auth = useAuthStore()
      try {
        await auth.refreshTokens()
        original.headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`
        return http(original)
      } catch {
        auth.logout()
        return navigateTo('/login')
      }
    }
    return Promise.reject(error)
  }
)

export default http
