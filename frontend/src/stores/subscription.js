import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { subscriptionApi } from '@/api/subscription'

export const useSubscriptionStore = defineStore('subscription', () => {
  const data = ref(null)

  // ASCN токены (energy)
  const energyLeft = computed(() => data.value?.energy_left ?? 0)
  const energyPerWeek = computed(() => data.value?.energy_per_week ?? 100)
  const energyPercent = computed(() =>
    energyPerWeek.value > 0
      ? Math.min(100, Math.round((energyLeft.value / energyPerWeek.value) * 100))
      : 0
  )

  // Собственные токены платформы
  const tokensLeft = computed(() => data.value?.tokens_left ?? 0)
  const tokensPerMonth = computed(() => data.value?.tokens_per_month ?? 0)
  const tokensPercent = computed(() =>
    tokensPerMonth.value > 0
      ? Math.min(100, Math.round((tokensLeft.value / tokensPerMonth.value) * 100))
      : 0
  )

  // Текущий тарифный план
  const tariffPlan = computed(() => data.value?.tariff_plan ?? null)
  const planName = computed(() => tariffPlan.value?.name ?? data.value?.plan_name ?? data.value?.plan ?? 'Бесплатный')

  // Долларовый баланс в центах → строка "$X.XX"
  const balanceUsd = computed(() => data.value?.balance_usd ?? 0)
  const balanceFormatted = computed(() => `$${(balanceUsd.value / 100).toFixed(2)}`)

  // Лимиты (из подписки)
  const maxAgents = computed(() => data.value?.max_agents ?? 1)
  const maxToolsPerAgent = computed(() => data.value?.max_tools_per_agent ?? 2)
  const maxKnowledgeBases = computed(() => data.value?.tariff_plan?.max_knowledge_bases ?? 1)

  async function fetch() {
    try {
      const res = await subscriptionApi.get()
      data.value = res.data
    } catch {}
  }

  function setEnergyLeft(value) {
    if (data.value) data.value.energy_left = value
  }

  return {
    data,
    energyLeft, energyPerWeek, energyPercent,
    tokensLeft, tokensPerMonth, tokensPercent,
    tariffPlan, planName,
    balanceUsd, balanceFormatted,
    maxAgents, maxToolsPerAgent, maxKnowledgeBases,
    fetch, setEnergyLeft,
  }
})
