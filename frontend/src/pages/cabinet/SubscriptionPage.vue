<template>
  <div class="p-6 max-w-3xl mx-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Подписка</h1>
      <p class="text-sm text-gray-400 mt-1">Ваш тарифный план, токены и баланс</p>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <template v-else>
      <!-- Текущий тариф -->
      <div class="card p-5 mb-4">
        <div class="flex items-start justify-between">
          <div>
            <div class="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Текущий тариф</div>
            <div class="text-xl font-bold text-gray-900">{{ subStore.planName }}</div>
            <div v-if="sub?.tariff_plan?.description" class="text-sm text-gray-500 mt-1">
              {{ sub.tariff_plan.description }}
            </div>
            <div v-if="sub?.tariff_plan?.price_usd === 0" class="mt-1 inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-green-50 text-green-700 border border-green-200">
              Бесплатно
            </div>
            <div v-else-if="sub?.tariff_plan?.price_usd" class="mt-1 text-sm text-gray-600">
              ${{ (sub.tariff_plan.price_usd / 100).toFixed(2) }} / месяц
            </div>
          </div>
          <div class="shrink-0 text-right">
            <div class="text-xs text-gray-400 mb-1">ASCN план</div>
            <div class="text-sm font-mono text-gray-600">{{ sub?.plan ?? '—' }}</div>
          </div>
        </div>

        <!-- Лимиты тарифа -->
        <div v-if="sub?.tariff_plan" class="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-gray-100">
          <div class="text-center">
            <div class="text-2xl font-bold text-primary-600">{{ sub.tariff_plan.max_agents }}</div>
            <div class="text-xs text-gray-400 mt-0.5">агентов</div>
          </div>
          <div class="text-center border-x border-gray-100">
            <div class="text-2xl font-bold text-primary-600">{{ sub.tariff_plan.max_tools_per_agent }}</div>
            <div class="text-xs text-gray-400 mt-0.5">инструм./агент</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-primary-600">{{ sub.tariff_plan.max_workflows }}</div>
            <div class="text-xs text-gray-400 mt-0.5">воркфлоу</div>
          </div>
        </div>
        <div v-else class="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-gray-100">
          <div class="text-center">
            <div class="text-2xl font-bold text-gray-700">{{ sub?.max_agents ?? 1 }}</div>
            <div class="text-xs text-gray-400 mt-0.5">агентов</div>
          </div>
          <div class="text-center border-l border-gray-100">
            <div class="text-2xl font-bold text-gray-700">{{ sub?.max_tools_per_agent ?? 2 }}</div>
            <div class="text-xs text-gray-400 mt-0.5">инструм./агент</div>
          </div>
        </div>
      </div>

      <!-- Токены и баланс -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">

        <!-- Agents Token -->
        <div class="card p-5">
          <div class="flex items-center justify-between mb-3">
            <div class="text-xs font-medium text-gray-500 uppercase tracking-wider">Agents Token</div>
            <span class="text-xs px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">platform</span>
          </div>
          <div class="flex items-baseline gap-2 mb-2">
            <span class="text-3xl font-bold text-gray-900">{{ subStore.tokensLeft.toLocaleString('ru') }}</span>
            <span class="text-sm text-gray-400">/ {{ subStore.tokensPerMonth.toLocaleString('ru') }} в месяц</span>
          </div>
          <div class="w-full bg-gray-100 rounded-full h-2">
            <div
              class="h-2 rounded-full transition-all"
              :class="subStore.tokensPercent > 20 ? 'bg-purple-500' : 'bg-red-400'"
              :style="{ width: subStore.tokensPercent + '%' }"
            />
          </div>
          <p class="text-xs text-gray-400 mt-2">
            Списываются при запуске инструментов и воркфлоу
          </p>
        </div>
      </div>

      <!-- ИИ-баланс -->
      <div class="card p-5 mb-4">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Баланс ИИ</div>
            <div class="text-3xl font-bold text-gray-900">{{ subStore.balanceFormatted }}</div>
            <p class="text-xs text-gray-400 mt-1">Списывается при использовании ИИ-оператора в инструментах</p>
          </div>
          <div class="text-4xl opacity-20">🤖</div>
        </div>
      </div>

      <!-- Доступные тарифы -->
      <div v-if="plans.length" class="mt-6">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-gray-900">Доступные тарифы</h2>
          <a
            href="https://ascn.ai/pricing"
            target="_blank"
            class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-primary-500 to-purple-500 text-white text-sm font-medium hover:opacity-90 transition-opacity"
          >Получить подписку</a>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div
            v-for="plan in plans"
            :key="plan.id"
            class="card p-4 border-2 transition-colors"
            :class="sub?.tariff_plan?.id === plan.id ? 'border-primary-400 bg-primary-50/30' : 'border-transparent hover:border-gray-200'"
          >
            <div class="flex items-start justify-between mb-2">
              <div class="font-semibold text-gray-900">{{ plan.name }}</div>
              <div v-if="sub?.tariff_plan?.id === plan.id" class="text-xs text-primary-600 font-medium">Текущий</div>
            </div>
            <div v-if="plan.description" class="text-xs text-gray-500 mb-3">{{ plan.description }}</div>
            <div class="space-y-1 text-xs text-gray-600">
              <div>👤 {{ plan.max_agents }} агентов</div>
              <div>🔧 {{ plan.max_tools_per_agent }} инструм./агент</div>
              <div>⟨⟩ {{ plan.max_workflows }} воркфлоу</div>
              <div>🗃️ {{ plan.max_knowledge_bases }} баз знаний</div>
              <div>🪙 {{ plan.tokens_per_month.toLocaleString('ru') }} Agents Token/мес</div>
              <div v-if="plan.balance_usd_per_month > 0">🤖 ${{ (plan.balance_usd_per_month / 100).toFixed(2) }} AI баланс/мес</div>
            </div>
            <div class="mt-3 pt-3 border-t border-gray-100">
              <div v-if="plan.price_usd === 0" class="text-sm font-semibold text-green-700">Бесплатно</div>
              <div v-else class="text-sm font-semibold text-gray-900">${{ (plan.price_usd / 100).toFixed(2) }}/мес</div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSubscriptionStore } from '@/stores/subscription'
import { subscriptionApi } from '@/api/subscription'

const subStore = useSubscriptionStore()
const loading = ref(true)
const plans = ref([])

const sub = computed(() => subStore.data)

onMounted(async () => {
  try {
    await Promise.all([
      subStore.fetch(),
      subscriptionApi.plans().then(r => { plans.value = r.data }),
    ])
  } catch {}
  loading.value = false
})
</script>
