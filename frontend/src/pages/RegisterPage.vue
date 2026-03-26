<template>
  <div class="min-h-screen bg-gradient-to-br from-primary-50 to-blue-50 flex items-center justify-center p-4">
    <div class="card w-full max-w-md p-8">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Создать аккаунт</h1>
      <p class="text-gray-500 text-sm mb-6">Начните пользоваться ИИ-агентами прямо сейчас</p>

      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="label">Имя</label>
          <input v-model="form.name" type="text" class="input" placeholder="Иван Иванов" required />
        </div>
        <div>
          <label class="label">Email</label>
          <input v-model="form.email" type="email" class="input" placeholder="you@example.com" required />
        </div>
        <div>
          <label class="label">Пароль</label>
          <input v-model="form.password" type="password" class="input" placeholder="Минимум 8 символов" required minlength="8" />
        </div>
        <button type="submit" class="btn-primary w-full justify-center" :disabled="loading">
          <span v-if="loading">Создаю аккаунт...</span>
          <span v-else>Зарегистрироваться</span>
        </button>
      </form>

      <p class="mt-4 text-sm text-center text-gray-500">
        Уже есть аккаунт?
        <RouterLink to="/login" class="text-primary-600 hover:underline font-medium">Войти</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const form = ref({ name: '', email: '', password: '' })
const loading = ref(false)

async function handleRegister() {
  loading.value = true
  try {
    await auth.register(form.value)
    router.push('/cabinet/office')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка регистрации')
  } finally {
    loading.value = false
  }
}
</script>
