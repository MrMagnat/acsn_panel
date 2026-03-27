import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware(() => {
  const auth = useAuthStore()
  if (!auth.user?.is_admin) {
    return navigateTo('/cabinet/office')
  }
})
