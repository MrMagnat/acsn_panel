import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { subscriptionApi } from '@/api/subscription'

export const useSubscriptionStore = defineStore('subscription', () => {
  const data = ref(null)

  const energyLeft = computed(() => data.value?.energy_left ?? 0)
  const energyPerWeek = computed(() => data.value?.energy_per_week ?? 100)
  const energyPercent = computed(() =>
    energyPerWeek.value > 0
      ? Math.min(100, Math.round((energyLeft.value / energyPerWeek.value) * 100))
      : 0
  )

  async function fetch() {
    try {
      const res = await subscriptionApi.get()
      data.value = res.data
    } catch {}
  }

  // Обновляем только energy_left без запроса к серверу
  function setEnergyLeft(value) {
    if (data.value) data.value.energy_left = value
  }

  return { data, energyLeft, energyPerWeek, energyPercent, fetch, setEnergyLeft }
})
