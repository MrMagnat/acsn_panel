<template>
  <div class="flex flex-col flex-1">
    <!-- Настройки модели -->
    <div class="px-4 py-2 border-b border-gray-100 flex items-center gap-2">
      <select v-model="selectedModel" class="text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-700 flex-1 min-w-0">
        <option value="">— Выберите модель —</option>
        <optgroup label="🆓 Бесплатные">
          <option value="google/gemini-2.0-flash-exp:free">Gemini 2.0 Flash (бесплатно)</option>
          <option value="deepseek/deepseek-r1:free">DeepSeek R1 (бесплатно)</option>
          <option value="deepseek/deepseek-chat-v3-0324:free">DeepSeek V3 (бесплатно)</option>
          <option value="meta-llama/llama-3.3-70b-instruct:free">Llama 3.3 70B (бесплатно)</option>
          <option value="meta-llama/llama-3.1-8b-instruct:free">Llama 3.1 8B (бесплатно)</option>
          <option value="mistralai/mistral-7b-instruct:free">Mistral 7B (бесплатно)</option>
          <option value="qwen/qwen-2.5-72b-instruct:free">Qwen 2.5 72B (бесплатно)</option>
        </optgroup>
        <optgroup label="OpenAI">
          <option value="openai/gpt-4o">GPT-4o</option>
          <option value="openai/gpt-4o-mini">GPT-4o Mini</option>
          <option value="openai/gpt-4.5-preview">GPT-4.5 Preview</option>
          <option value="openai/o3-mini">o3-mini</option>
          <option value="openai/o1">o1</option>
        </optgroup>
        <optgroup label="Anthropic">
          <option value="anthropic/claude-3-7-sonnet">Claude 3.7 Sonnet</option>
          <option value="anthropic/claude-3-5-sonnet">Claude 3.5 Sonnet</option>
          <option value="anthropic/claude-3-5-haiku">Claude 3.5 Haiku</option>
          <option value="anthropic/claude-3-opus">Claude 3 Opus</option>
        </optgroup>
        <optgroup label="Google">
          <option value="google/gemini-2.0-flash-001">Gemini 2.0 Flash</option>
          <option value="google/gemini-2.0-pro-exp-02-05">Gemini 2.0 Pro</option>
          <option value="google/gemini-flash-1.5">Gemini 1.5 Flash</option>
          <option value="google/gemini-pro-1.5">Gemini 1.5 Pro</option>
        </optgroup>
        <optgroup label="DeepSeek">
          <option value="deepseek/deepseek-r1">DeepSeek R1</option>
          <option value="deepseek/deepseek-chat-v3-0324">DeepSeek V3</option>
        </optgroup>
        <optgroup label="Meta / Open Source">
          <option value="meta-llama/llama-3.3-70b-instruct">Llama 3.3 70B</option>
          <option value="mistralai/mistral-large">Mistral Large</option>
          <option value="mistralai/mistral-small-3.1-24b-instruct">Mistral Small 3.1</option>
          <option value="qwen/qwen-2.5-72b-instruct">Qwen 2.5 72B</option>
        </optgroup>
      </select>
      <div class="relative flex-1 min-w-0">
        <input
          v-model="apiKey"
          :type="showKey ? 'text' : 'password'"
          class="text-xs border border-gray-200 rounded-lg px-2 py-1 w-full pr-7"
          placeholder="sk-or-v1-..."
        />
        <button class="absolute right-1.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600" @click="showKey = !showKey">
          {{ showKey ? '🙈' : '👁' }}
        </button>
      </div>
    </div>

    <!-- История сообщений -->
    <div ref="scrollEl" class="flex-1 overflow-y-auto p-4 space-y-3" style="min-height: 300px; max-height: 400px">
      <div v-if="loading" class="text-center text-gray-400 py-4 text-sm">Загрузка истории...</div>

      <template v-for="msg in messages" :key="msg.id">
        <!-- Системное сообщение инструмента -->
        <div v-if="msg.role === 'tool'" class="flex justify-center">
          <div class="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-500 max-w-sm">
            🔧 <span class="font-medium">{{ msg.tool_name }}</span> вызван
          </div>
        </div>

        <!-- Сообщение пользователя -->
        <div v-else-if="msg.role === 'user'" class="flex justify-end">
          <div class="bg-primary-500 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm max-w-xs lg:max-w-md">
            {{ msg.content }}
          </div>
        </div>

        <!-- Ответ ассистента -->
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

    <!-- Информация о потраченной энергии -->
    <div v-if="lastEnergySpent" class="px-4 py-1 text-xs text-gray-400 text-right border-t border-gray-50">
      Потрачено ⚡{{ lastEnergySpent }}, осталось ⚡{{ currentEnergyLeft }}
    </div>

    <!-- Поле ввода -->
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
import { chatApi } from '@/api/chat'
import { useToastStore } from '@/stores/toast'
import { useSubscriptionStore } from '@/stores/subscription'

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
const selectedModel = ref(localStorage.getItem(`chat_model_${props.agentId}`) || '')
const apiKey = ref(localStorage.getItem(`chat_key_${props.agentId}`) || '')
const showKey = ref(false)

watch(selectedModel, (v) => localStorage.setItem(`chat_model_${props.agentId}`, v))
watch(apiKey, (v) => localStorage.setItem(`chat_key_${props.agentId}`, v))

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
    const res = await chatApi.sendMessage(props.agentId, text, selectedModel.value || undefined, apiKey.value || undefined)
    messages.value.push(...res.data.messages)
    lastEnergySpent.value = res.data.energy_spent
    currentEnergyLeft.value = res.data.energy_left
    subStore.setEnergyLeft(res.data.energy_left)  // обновляем сайдбар мгновенно
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
