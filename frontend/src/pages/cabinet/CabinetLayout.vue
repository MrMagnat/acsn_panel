<template>
  <div class="min-h-screen flex bg-surface">
    <!-- Боковое меню -->
    <aside class="w-60 bg-white border-r border-gray-100 flex flex-col shrink-0">
      <div class="px-6 py-5 border-b border-gray-100">
        <span class="text-xl font-bold text-primary-600">ASCN</span>
        <span class="text-xs text-gray-400 ml-1">AI Platform</span>
      </div>

      <nav class="flex-1 px-3 py-4 space-y-1">
        <RouterLink id="nav-office" to="/cabinet/office" class="nav-link" active-class="nav-link--active">
          <span>🏠</span> Мой офис
        </RouterLink>
        <RouterLink id="nav-tools" to="/cabinet/tools" class="nav-link" active-class="nav-link--active">
          <span>🔧</span> Инструменты
        </RouterLink>
        <RouterLink id="nav-history" to="/cabinet/history" class="nav-link" active-class="nav-link--active">
          <span>📋</span> История запусков
        </RouterLink>
        <RouterLink to="/cabinet/knowledge-base" class="nav-link" active-class="nav-link--active">
          <span>🗃️</span> База знаний
        </RouterLink>
        <template v-if="auth.user?.is_admin">
          <div class="border-t border-gray-100 my-2"></div>
          <RouterLink to="/admin" class="nav-link text-purple-600" active-class="nav-link--active">
            <span>🔑</span> Админ панель
          </RouterLink>
        </template>
      </nav>

      <!-- Энергия аккаунта -->
      <div v-if="subStore.data" id="user-energy" class="px-4 py-3 border-t border-gray-100">
        <div class="flex justify-between items-center mb-1">
          <span class="text-xs text-gray-500">⚡ Токены</span>
          <span class="text-xs font-medium text-gray-700">{{ subStore.energyLeft }} / {{ subStore.energyPerWeek }}</span>
        </div>
        <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all"
            :class="subStore.energyPercent > 30 ? 'bg-green-400' : subStore.energyPercent > 10 ? 'bg-yellow-400' : 'bg-red-400'"
            :style="{ width: subStore.energyPercent + '%' }"
          ></div>
        </div>
        <div class="text-xs text-gray-400 mt-1">Обновляется раз в неделю</div>
        <!-- Долларовый баланс (AI-токены) -->
        <div class="flex justify-between items-center mt-2 pt-2 border-t border-gray-100">
          <span class="text-xs text-gray-500">🤖 AI баланс</span>
          <span class="text-xs font-medium" :class="subStore.balanceUsd > 0 ? 'text-green-600' : 'text-red-400'">
            {{ subStore.balanceFormatted }}
          </span>
        </div>
      </div>

      <div class="px-4 py-4 border-t border-gray-100">
        <div class="text-xs text-gray-500 mb-1">{{ auth.user?.name }}</div>
        <div class="text-xs text-gray-400 mb-3">{{ auth.user?.email }}</div>
        <div class="flex gap-2">
          <button class="btn-secondary text-xs flex-1 justify-center" @click="handleLogout">Выйти</button>
          <button
            class="text-xs px-2 py-1.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
            title="Помощь"
            @click="openHelp"
          >❓</button>
        </div>
      </div>
    </aside>

    <!-- Основной контент -->
    <main class="flex-1 overflow-auto">
      <RouterView />
    </main>

    <!-- Онбординг -->
    <OnboardingWelcomeModal
      v-if="onb.showWelcome.value"
      :support-url="onb.config.value?.support_url"
      @start="onb.startTour()"
      @skip="onb.closeWelcome()"
    />
    <OnboardingVideoModal
      v-if="onb.showVideo.value"
      :video-url="onb.config.value?.video_url"
      @close="onb.showVideo.value = false"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { useSubscriptionStore } from '@/stores/subscription'
import { useOnboarding } from '@/composables/useOnboarding'
import OnboardingWelcomeModal from '@/components/onboarding/OnboardingWelcomeModal.vue'
import OnboardingVideoModal from '@/components/onboarding/OnboardingVideoModal.vue'

const auth = useAuthStore()
const router = useRouter()
const subStore = useSubscriptionStore()
const onb = useOnboarding()

onMounted(async () => {
  subStore.fetch()
  await onb.loadConfig()
  onb.checkAutoShow()
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}

function openHelp() {
  onb.openWelcome()
}
</script>

<style scoped>
.nav-link {
  @apply flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors;
}
.nav-link--active {
  @apply bg-primary-50 text-primary-700 font-medium;
}
</style>
