<template>
  <div class="min-h-screen bg-gradient-to-br from-primary-50 to-blue-50 flex items-center justify-center p-4">
    <div class="card w-full max-w-md p-8">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Войти в ASCN</h1>
      <p class="text-gray-500 text-sm mb-6">AI-платформа для управления агентами</p>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="label">Email</label>
          <input v-model="form.email" type="email" class="input" placeholder="you@example.com" required />
        </div>
        <div>
          <label class="label">Пароль</label>
          <input v-model="form.password" type="password" class="input" placeholder="••••••••" required />
        </div>
        <button type="submit" class="btn-primary w-full justify-center" :disabled="loading">
          <span v-if="loading">Вхожу...</span>
          <span v-else>Войти</span>
        </button>
      </form>

      <p class="mt-4 text-sm text-center text-gray-500">
        Нет аккаунта?
        <a href="https://ascn.ai/register" class="text-primary-600 hover:underline font-medium">Зарегистрироваться на ASCN</a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const form = ref({ email: '', password: '' })
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    await auth.ascnLogin(form.value.email, form.value.password)
    const redirect = route.query.redirect || '/cabinet/office'
    router.push(redirect)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Неверный email или пароль')
  } finally {
    loading.value = false
  }
}
</script>
