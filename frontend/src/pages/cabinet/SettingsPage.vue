<template>
  <div class="p-8 max-w-lg mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Настройки</h1>

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
import { subscriptionApi } from '@/api/subscription'

const subscription = ref(null)

onMounted(async () => {
  const res = await subscriptionApi.get()
  subscription.value = res.data
})
</script>
