<template>
  <div class="flex flex-col flex-1">
    <div ref="scrollEl" class="flex-1 overflow-y-auto p-4 space-y-3" style="min-height: 300px; max-height: 400px">
      <div v-if="loading" class="text-center text-gray-400 py-4 text-sm">Загрузка истории...</div>

      <template v-for="msg in messages" :key="msg.id">
        <div v-if="msg.role === 'tool'" class="flex justify-center">
          <div class="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-500 max-w-sm">
            🔧 <span class="font-medium">{{ msg.tool_name }}</span> вызван
          </div>
        </div>

        <div v-else-if="msg.role === 'user'" class="flex justify-end">
          <div class="bg-primary-500 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm max-w-xs lg:max-w-md">
            {{ msg.content }}
          </div>
        </div>

        <div v-else class="flex justify-start">
          <div class="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm max-w-xs lg:max-w-md shadow-sm">
            {{ msg.content }}
          </div>
        </div>
      </template>

      <div v-if="messages.length === 0 && !loading" class="text-center text-gray-300 py-8 text-sm">
        Начните диалог с агентом
      </div>
    </div>

    <div v-if="lastEnergySpent" class="px-4 py-1 text-xs text-gray-400 text-right border-t border-gray-50">
      Потрачено ⚡{{ lastEnergySpent }}, осталось ⚡{{ currentEnergyLeft }}
    </div>

    <div class="px-4 py-3 border-t border-gray-100 flex gap-2">
      <input
        v-model="inputText"
        class="input flex-1"
        placeholder="Напишите сообщение..."
        :disabled="sending"
        @keydown.enter.prevent="sendMessage"
      />
      <button
        class="btn-primary"
        :disabled="sending || !inputText.trim()"
        @click="sendMessage"
      >
        {{ sending ? '...' : 'Отправить' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { chatApi } from '~/api/chat'
import { useToastStore } from '~/stores/toast'
import { useSubscriptionStore } from '~/stores/subscription'

const props = defineProps({
  agentId: { type: String, required: true },
  energyLeft: { type: Number, default: 0 },
})
const emit = defineEmits(['energy-updated'])

const toast = useToastStore()
const subStore = useSubscriptionStore()
const messages = ref([])
const loading = ref(true)
const sending = ref(false)
const inputText = ref('')
const scrollEl = ref(null)
const lastEnergySpent = ref(0)
const currentEnergyLeft = ref(props.energyLeft)

watch(() => props.energyLeft, (v) => { currentEnergyLeft.value = v })

onMounted(async () => {
  try {
    const res = await chatApi.getHistory(props.agentId)
    messages.value = res.data
    await scrollToBottom()
  } finally {
    loading.value = false
  }
})

async function sendMessage() {
  if (!inputText.value.trim() || sending.value) return

  const text = inputText.value.trim()
  inputText.value = ''
  sending.value = true

  try {
    const res = await chatApi.sendMessage(props.agentId, text)
    messages.value.push(...res.data.messages)
    lastEnergySpent.value = res.data.energy_spent
    currentEnergyLeft.value = res.data.energy_left
    subStore.setEnergyLeft(res.data.energy_left)
    emit('energy-updated', res.data.energy_left)
    await scrollToBottom()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка отправки сообщения')
  } finally {
    sending.value = false
  }
}

async function scrollToBottom() {
  await nextTick()
  if (scrollEl.value) {
    scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  }
}
</script>
