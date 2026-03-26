import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// Базовый экземпляр axios
const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
})

// Добавляем JWT токен к каждому запросу
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Обработка 401 — пробуем обновить токен
http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const auth = useAuthStore()
      try {
        await auth.refreshTokens()
        original.headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`
        return http(original)
      } catch {
        auth.logout()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default http
