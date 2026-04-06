<template>
  <div class="p-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Мой офис</h1>
      <p class="text-gray-500 text-sm mt-1">Управляйте вашими ИИ-агентами</p>
    </div>

    <!-- Галерея агентов -->
    <div v-if="agentsStore.loading" class="flex justify-center py-16">
      <div class="text-gray-400">Загрузка...</div>
    </div>

    <div v-else id="agent-list" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <!-- Плитки существующих агентов -->
      <AgentCard
        v-for="agent in agentsStore.agents"
        :key="agent.id"
        :agent="agent"
        @click="router.push(`/cabinet/agents/${agent.id}`)"
      />

      <!-- Плитка добавления агента -->
      <button
        id="add-agent-btn"
        class="card p-6 flex flex-col items-center justify-center gap-3 border-2 border-dashed border-gray-200 hover:border-primary-400 hover:bg-primary-50 transition-colors min-h-[160px] cursor-pointer"
        @click="handleAddClick"
      >
        <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-2xl text-primary-500">+</div>
        <span class="text-sm font-medium text-gray-600">Добавить агента</span>
        <span class="text-xs text-gray-400">{{ agentsStore.agents.length }} / {{ subStore.data?.max_agents ?? 1 }}</span>
      </button>
    </div>

    <!-- Модал добавления агента -->
    <AddAgentModal
      v-if="showAddModal"
      @close="showAddModal = false"
      @created="handleAgentCreated"
    />

    <!-- Попап: лимит агентов -->
    <UpgradePlanModal
      v-if="showUpgradeModal"
      title="Лимит агентов достигнут"
      description="На вашем тарифе недоступно добавление новых агентов. Повысьте тариф, чтобы создавать больше ИИ-агентов."
      @close="showUpgradeModal = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentsStore } from '@/stores/agents'
import { useSubscriptionStore } from '@/stores/subscription'
import AgentCard from '@/components/agents/AgentCard.vue'
import AddAgentModal from '@/components/agents/AddAgentModal.vue'
import UpgradePlanModal from '@/components/UpgradePlanModal.vue'

const router = useRouter()
const agentsStore = useAgentsStore()
const subStore = useSubscriptionStore()
const showAddModal = ref(false)
const showUpgradeModal = ref(false)

onMounted(async () => {
  await agentsStore.fetchAgents()
})

function handleAddClick() {
  const limit = subStore.data?.max_agents ?? 1
  if (agentsStore.agents.length >= limit) {
    showUpgradeModal.value = true
  } else {
    showAddModal.value = true
  }
}

function handleAgentCreated() {
  showAddModal.value = false
}
</script>
