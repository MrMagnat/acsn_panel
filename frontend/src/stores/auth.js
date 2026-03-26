import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  const isAuthenticated = computed(() => !!accessToken.value)

  function _saveTokens(tokens) {
    accessToken.value = tokens.access_token
    refreshToken.value = tokens.refresh_token
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
  }

  async function register(data) {
    const res = await authApi.register(data)
    _saveTokens(res.data)
    await fetchMe()
  }

  async function login(data) {
    const res = await authApi.login(data)
    _saveTokens(res.data)
    await fetchMe()
  }

  async function refreshTokens() {
    const res = await authApi.refresh(refreshToken.value)
    _saveTokens(res.data)
  }

  async function fetchMe() {
    const res = await authApi.me()
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
  }

  function logout() {
    user.value = null
    accessToken.value = ''
    refreshToken.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  return { user, isAuthenticated, register, login, logout, refreshTokens, fetchMe }
})
