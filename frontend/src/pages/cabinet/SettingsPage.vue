<template>
  <div class="p-8 max-w-lg mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Настройки</h1>

    <!-- Профиль -->
    <div class="card p-6 mb-4">
      <h2 class="font-semibold text-gray-700 mb-4">Профиль</h2>
      <form @submit.prevent="saveProfile" class="space-y-4">
        <div>
          <label class="label">Имя</label>
          <input v-model="profile.name" class="input" required />
        </div>
        <div>
          <label class="label">Email</label>
          <input :value="auth.user?.email" class="input" disabled />
          <p class="text-xs text-gray-400 mt-1">Email изменить нельзя</p>
        </div>
        <button type="submit" class="btn-primary" :disabled="savingProfile">
          {{ savingProfile ? 'Сохраняю...' : 'Сохранить' }}
        </button>
      </form>
    </div>

    <!-- Смена пароля -->
    <div class="card p-6 mb-4">
      <h2 class="font-semibold text-gray-700 mb-4">Смена пароля</h2>
      <form @submit.prevent="changePassword" class="space-y-4">
        <div>
          <label class="label">Новый пароль</label>
          <input v-model="passwords.new" type="password" class="input" minlength="8" required />
        </div>
        <div>
          <label class="label">Повторите пароль</label>
          <input v-model="passwords.confirm" type="password" class="input" required />
        </div>
        <button type="submit" class="btn-primary" :disabled="savingPassword">
          {{ savingPassword ? 'Меняю...' : 'Изменить пароль' }}
        </button>
      </form>
    </div>

    <!-- Подписка -->
    <div class="card p-6">
      <h2 class="font-semibold text-gray-700 mb-4">Подписка</h2>
      <div v-if="subscription" class="space-y-2 text-sm text-gray-600">
        <div class="flex justify-between">
          <span>Тариф</span>
          <span class="font-semibold capitalize">{{ subscription.plan }}</span>
        </div>
        <div class="flex justify-between">
          <span>Агентов</span>
          <span>до {{ subscription.max_agents }}</span>
        </div>
        <div class="flex justify-between">
          <span>Инструментов на агента</span>
          <span>до {{ subscription.max_tools_per_agent }}</span>
        </div>
        <div class="flex justify-between">
          <span>Энергия в неделю</span>
          <span>{{ subscription.energy_per_week }} ⚡</span>
        </div>
      </div>
      <a href="#" class="btn-secondary text-sm mt-4 inline-block">Сменить тариф →</a>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { subscriptionApi } from '@/api/subscription'
import http from '@/api/http'

const auth = useAuthStore()
const toast = useToastStore()

const profile = ref({ name: auth.user?.name || '' })
const passwords = ref({ new: '', confirm: '' })
const subscription = ref(null)
const savingProfile = ref(false)
const savingPassword = ref(false)

onMounted(async () => {
  const res = await subscriptionApi.get()
  subscription.value = res.data
})

async function saveProfile() {
  savingProfile.value = true
  try {
    await http.patch('/auth/me', { name: profile.value.name })
    await auth.fetchMe()
    toast.success('Профиль обновлён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка обновления')
  } finally {
    savingProfile.value = false
  }
}

async function changePassword() {
  if (passwords.value.new !== passwords.value.confirm) {
    toast.error('Пароли не совпадают')
    return
  }
  savingPassword.value = true
  try {
    await http.patch('/auth/me', { password: passwords.value.new })
    passwords.value = { new: '', confirm: '' }
    toast.success('Пароль изменён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка смены пароля')
  } finally {
    savingPassword.value = false
  }
}
</script>
