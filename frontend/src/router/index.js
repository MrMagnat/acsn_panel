import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  // Публичные маршруты
  { path: '/login', name: 'Login', component: () => import('@/pages/LoginPage.vue') },
  { path: '/register', name: 'Register', component: () => import('@/pages/RegisterPage.vue') },

  // Личный кабинет
  {
    path: '/cabinet',
    component: () => import('@/pages/cabinet/CabinetLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/cabinet/office' },
      { path: 'office', name: 'Office', component: () => import('@/pages/cabinet/MyOfficePage.vue') },
      { path: 'agents/:id', name: 'AgentDetail', component: () => import('@/pages/cabinet/AgentDetailPage.vue') },
{ path: 'tools', name: 'ToolStore', component: () => import('@/pages/cabinet/ToolStorePage.vue') },
      { path: 'history', name: 'RunHistory', component: () => import('@/pages/cabinet/RunHistoryPage.vue') },
      { path: 'knowledge-base', name: 'KnowledgeBase', component: () => import('@/pages/cabinet/KnowledgeBasePage.vue') },
      { path: 'knowledge-base/:id', name: 'KnowledgeBaseDetail', component: () => import('@/pages/cabinet/KnowledgeBaseDetailPage.vue') },
    ],
  },

  // Админ панель
  {
    path: '/admin',
    component: () => import('@/pages/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/users' },
      { path: 'users', name: 'AdminUsers', component: () => import('@/pages/admin/AdminUsersPage.vue') },
      { path: 'agents', name: 'AdminAgents', component: () => import('@/pages/admin/AdminAgentsPage.vue') },
      { path: 'tools', name: 'AdminTools', component: () => import('@/pages/admin/AdminToolsPage.vue') },
      { path: 'onboarding', name: 'AdminOnboarding', component: () => import('@/pages/admin/AdminOnboardingPage.vue') },
      { path: 'ascn', name: 'AdminAscn', component: () => import('@/pages/admin/AdminAscnPage.vue') },
    ],
  },

  // Редирект с корня
  { path: '/', redirect: '/cabinet/office' },
  { path: '/:pathMatch(.*)*', redirect: '/cabinet/office' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Навигационный guard — проверяем авторизацию
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !auth.user?.is_admin) {
    return { name: 'Office' }
  }
})

export default router
