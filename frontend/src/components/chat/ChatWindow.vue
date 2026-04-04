<template>
  <div class="flex flex-col flex-1">
    <!-- Настройки модели -->
    <div class="px-4 py-2 border-b border-gray-100 flex flex-wrap items-center gap-2">
      <!-- Провайдер -->
      <select v-model="selectedProvider" class="text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-700 w-32 shrink-0">
        <option value="ascn">✦ ASCN</option>
        <option value="openrouter">OpenRouter</option>
        <option value="openai">OpenAI</option>
        <option value="anthropic">Anthropic</option>
        <option value="deepseek">DeepSeek</option>
        <option value="google">Google</option>
      </select>

      <!-- ASCN: модели с ценами + баланс -->
      <template v-if="selectedProvider === 'ascn'">
        <select v-model="selectedModel" class="text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-700 flex-1 min-w-0">
          <option value="">— модель —</option>
          <option v-for="m in ascnModels" :key="m.id" :value="m.id">
            {{ m.name }} — ${{ (m.price_usd / 100).toFixed(2) }}/сообщ.
          </option>
        </select>
        <span class="text-xs px-2 py-0.5 rounded-full" :class="subStore.balanceUsd > 0 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-500'">
          {{ subStore.balanceFormatted }}
        </span>
      </template>

      <!-- Другие провайдеры: обычный выбор модели + ключ -->
      <template v-else>
        <select v-model="selectedModel" class="text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-700 flex-1 min-w-0">
          <option value="">— модель —</option>
          <option v-for="m in providerModels" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
        <div class="relative w-full">
          <input
            v-model="apiKey"
            :type="showKey ? 'text' : 'password'"
            class="text-xs border border-gray-200 rounded-lg px-2 py-1 w-full pr-7"
            :placeholder="keyPlaceholder"
          />
          <button class="absolute right-1.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600" @click="showKey = !showKey">
            {{ showKey ? '🙈' : '👁' }}
          </button>
        </div>
      </template>
    </div>

    <!-- Попап: нулевой баланс -->
    <Teleport to="body">
      <div v-if="showBalancePopup" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-7 text-center">
          <div class="text-4xl mb-3">💳</div>
          <h2 class="text-lg font-bold text-gray-900 mb-2">Баланс AI-токенов исчерпан</h2>
          <p class="text-gray-500 text-sm mb-6">Пополните баланс или подключите собственный API-ключ</p>
          <div class="space-y-3">
            <a href="https://t.me/ascnai_nocode" target="_blank" class="btn-primary w-full justify-center flex" @click="showBalancePopup = false">
              💰 Пополнить баланс
            </a>
            <button class="w-full py-2 text-sm text-gray-400 hover:text-gray-600 border border-gray-200 rounded-xl transition-colors" @click="switchToOwnKey">
              Подключить свой ключ
            </button>
            <button class="text-xs text-gray-400 hover:text-gray-600 w-full" @click="showBalancePopup = false">Закрыть</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- История сообщений -->
    <div ref="scrollEl" class="flex-1 overflow-y-auto p-4 space-y-3" style="min-height: 300px; max-height: 400px">
      <div v-if="loading" class="text-center text-gray-400 py-4 text-sm">Загрузка истории...</div>

      <template v-for="msg in messages" :key="msg.id">
        <!-- Системное сообщение инструмента — кликабельная плашка -->
        <div v-if="msg.role === 'tool'" class="flex justify-center">
          <button
            class="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-500 hover:border-primary-300 hover:bg-primary-50 transition-colors"
            @click="msg.log_id && openLogPopup(msg.log_id)"
          >
            🔧 <span class="font-medium">{{ msg.tool_name }}</span>
            <span v-if="msg.log_id" class="ml-1 text-primary-500">— посмотреть результат →</span>
          </button>
        </div>

        <!-- Сообщение пользователя -->
        <div v-else-if="msg.role === 'user'" class="flex justify-end">
          <div class="bg-primary-500 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm max-w-xs lg:max-w-md">
            {{ msg.content }}
          </div>
        </div>

        <!-- Ответ ассистента -->
        <div v-else class="flex justify-start">
          <div class="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm max-w-xs lg:max-w-md shadow-sm prose prose-sm max-w-none"
            v-html="renderMarkdown(msg.content)">
          </div>
        </div>
      </template>

      <div v-if="messages.length === 0 && !loading" class="text-center text-gray-300 py-8 text-sm">
        Начните диалог с агентом
      </div>
    </div>

    <!-- Энергия -->
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

  <!-- Попап результата запуска (как при ручном ▶) -->
  <Teleport to="body">
    <div v-if="popupLogId" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="closePopup">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-md flex flex-col" style="max-height: 85vh;">
        <!-- Шапка -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
          <div class="flex items-center gap-2">
            <span v-if="popupLog?.status === 'running'" class="inline-block w-4 h-4 border-2 border-primary-400 border-t-transparent rounded-full animate-spin"></span>
            <span v-else-if="popupLog?.status === 'success'" class="text-green-500">✅</span>
            <span v-else-if="popupLog?.status === 'cancelled'" class="text-gray-400">⏹</span>
            <span v-else class="text-red-500">❌</span>
            <h3 class="font-semibold text-gray-900">{{ popupToolName }}</h3>
          </div>
          <button class="text-gray-400 hover:text-gray-600" @click="closePopup">✕</button>
        </div>

        <!-- Статус -->
        <div class="px-6 pt-4 pb-1 shrink-0">
          <span class="text-xs font-medium px-2 py-0.5 rounded-full"
            :class="{
              'bg-yellow-100 text-yellow-700': popupLog?.status === 'running',
              'bg-green-100 text-green-700': popupLog?.status === 'success',
              'bg-red-100 text-red-700': popupLog?.status === 'error',
              'bg-gray-100 text-gray-500': popupLog?.status === 'cancelled',
            }">
            {{ { running: 'Выполняется...', success: 'Выполнено', error: 'Ошибка', cancelled: 'Остановлено' }[popupLog?.status] ?? 'Запускаем...' }}
          </span>
          <span v-if="popupLog?.status === 'running'" class="text-xs text-gray-400 ml-2">обновляется каждые 2 сек...</span>
        </div>

        <!-- Результат -->
        <div class="px-6 py-4 overflow-y-auto flex-1">
          <ResultRenderer v-if="popupLog" :result-json="popupLog.result_json" :status="popupLog.status" />
          <div v-else class="flex items-center gap-2 text-sm text-gray-400 py-4">
            <span class="inline-block w-4 h-4 border-2 border-gray-300 border-t-transparent rounded-full animate-spin"></span>
            Задача запущена, ожидаем результат...
          </div>
        </div>

        <div class="px-6 pb-4 flex justify-between items-center">
          <button
            v-if="popupLog?.status === 'running'"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 transition-colors"
            :disabled="cancelling"
            @click="cancelPopup"
          >
            <span v-if="cancelling" class="inline-block w-3 h-3 border-2 border-red-400 border-t-transparent rounded-full animate-spin"></span>
            <span v-else>⏹</span>
            {{ cancelling ? 'Останавливаю...' : 'Остановить' }}
          </button>
          <div v-else></div>
          <button class="btn-secondary text-sm" @click="closePopup">Закрыть</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { marked } from 'marked'

const PROVIDER_MODELS = {
  openrouter: [
    { value: 'google/gemini-2.0-flash-exp:free', label: 'Gemini 2.0 Flash (free)' },
    { value: 'deepseek/deepseek-r1:free',         label: 'DeepSeek R1 (free)' },
    { value: 'deepseek/deepseek-chat-v3-0324:free', label: 'DeepSeek V3 (free)' },
    { value: 'meta-llama/llama-3.3-70b-instruct:free', label: 'Llama 3.3 70B (free)' },
    { value: 'mistralai/mistral-7b-instruct:free', label: 'Mistral 7B (free)' },
    { value: 'openai/gpt-4o',                     label: 'GPT-4o' },
    { value: 'openai/gpt-4o-mini',                label: 'GPT-4o Mini' },
    { value: 'anthropic/claude-3-7-sonnet',        label: 'Claude 3.7 Sonnet' },
    { value: 'anthropic/claude-3-5-sonnet',        label: 'Claude 3.5 Sonnet' },
    { value: 'google/gemini-2.0-flash-001',        label: 'Gemini 2.0 Flash' },
    { value: 'deepseek/deepseek-r1',               label: 'DeepSeek R1' },
    { value: 'meta-llama/llama-3.3-70b-instruct',  label: 'Llama 3.3 70B' },
    { value: 'mistralai/mistral-large',            label: 'Mistral Large' },
  ],
  openai: [
    { value: 'gpt-4o',           label: 'GPT-4o' },
    { value: 'gpt-4o-mini',      label: 'GPT-4o Mini' },
    { value: 'gpt-4.5-preview',  label: 'GPT-4.5 Preview' },
    { value: 'o3-mini',          label: 'o3-mini' },
    { value: 'o1',               label: 'o1' },
  ],
  anthropic: [
    { value: 'claude-3-7-sonnet-20250219', label: 'Claude 3.7 Sonnet' },
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
    { value: 'claude-3-5-haiku-20241022',  label: 'Claude 3.5 Haiku' },
    { value: 'claude-3-opus-20240229',     label: 'Claude 3 Opus' },
  ],
  deepseek: [
    { value: 'deepseek-chat',     label: 'DeepSeek V3 (Chat)' },
    { value: 'deepseek-reasoner', label: 'DeepSeek R1 (Reasoner)' },
  ],
  google: [
    { value: 'gemini-2.0-flash',   label: 'Gemini 2.0 Flash' },
    { value: 'gemini-2.0-pro-exp', label: 'Gemini 2.0 Pro' },
    { value: 'gemini-1.5-flash',   label: 'Gemini 1.5 Flash' },
    { value: 'gemini-1.5-pro',     label: 'Gemini 1.5 Pro' },
  ],
}

const KEY_PLACEHOLDERS = {
  openrouter: 'sk-or-v1-...',
  openai:     'sk-...',
  anthropic:  'sk-ant-...',
  deepseek:   'sk-...',
  google:     'AIza...',
}
import { chatApi } from '@/api/chat'
import { agentsApi } from '@/api/agents'
import http from '@/api/http'
import { useToastStore } from '@/stores/toast'
import { useSubscriptionStore } from '@/stores/subscription'
import ResultRenderer from '@/components/tools/ResultRenderer.vue'

const props = defineProps({
  agentId: { type: String, required: true },
  energyLeft: { type: Number, default: 0 },
})
const emit = defineEmits(['energy-updated', 'trigger-created', 'tool-run', 'settings-saved'])

const toast = useToastStore()
const subStore = useSubscriptionStore()
const messages = ref([])
const loading = ref(true)
const sending = ref(false)
const inputText = ref('')
const scrollEl = ref(null)
const lastEnergySpent = ref(0)
const currentEnergyLeft = ref(props.energyLeft)
const selectedProvider = ref(localStorage.getItem(`chat_provider_${props.agentId}`) || 'ascn')
const selectedModel = ref(localStorage.getItem(`chat_model_${props.agentId}`) || '')
const apiKey = ref(localStorage.getItem(`chat_key_${props.agentId}`) || '')
const showKey = ref(false)
const showBalancePopup = ref(false)
const ascnModels = ref([])

const providerModels = computed(() => PROVIDER_MODELS[selectedProvider.value] || [])
const keyPlaceholder = computed(() => KEY_PLACEHOLDERS[selectedProvider.value] || 'API key...')


function switchToOwnKey() {
  showBalancePopup.value = false
  selectedProvider.value = 'openrouter'
  selectedModel.value = ''
}

// Попап результата
const popupLogId = ref(null)
const popupLog = ref(null)
const popupToolName = ref('')
const cancelling = ref(false)
let popupPollTimer = null

watch(selectedProvider, (v) => {
  localStorage.setItem(`chat_provider_${props.agentId}`, v)
  // сбрасываем модель если не подходит для нового провайдера
  const models = PROVIDER_MODELS[v] || []
  if (!models.find(m => m.value === selectedModel.value)) selectedModel.value = ''
})
watch(selectedModel, (v) => localStorage.setItem(`chat_model_${props.agentId}`, v))
watch(apiKey, (v) => localStorage.setItem(`chat_key_${props.agentId}`, v))
watch(() => props.energyLeft, (v) => { currentEnergyLeft.value = v })

onMounted(async () => {
  // Загружаем ASCN-модели
  try {
    const res = await http.get('/onboarding/ascn-models')
    ascnModels.value = res.data
    if (!selectedModel.value && selectedProvider.value === 'ascn' && ascnModels.value.length) {
      selectedModel.value = ascnModels.value[0].id
    }
  } catch { /**/ }
  // История чата
  try {
    const res = await chatApi.getHistory(props.agentId)
    messages.value = res.data
    await scrollToBottom()
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (popupPollTimer) clearInterval(popupPollTimer)
})

async function openLogPopup(logId) {
  popupLogId.value = logId
  popupLog.value = null
  const msg = messages.value.find(m => m.log_id === logId)
  popupToolName.value = msg?.tool_name || 'Инструмент'
  await fetchPopupLog(logId)
  if (popupLog.value?.status === 'running') {
    popupPollTimer = setInterval(async () => {
      await fetchPopupLog(logId)
      if (popupLog.value?.status !== 'running') {
        clearInterval(popupPollTimer)
        popupPollTimer = null
      }
    }, 2000)
  }
}

async function fetchPopupLog(logId) {
  try {
    const res = await agentsApi.pollRunLog(logId)
    const prev = popupLog.value?.status
    popupLog.value = res.data
    // Когда статус изменился с running на финальный — обновляем историю
    if (prev === 'running' && res.data.status !== 'running') emit('tool-run')
  } catch { /* тихо */ }
}

function closePopup() {
  if (popupPollTimer) { clearInterval(popupPollTimer); popupPollTimer = null }
  popupLogId.value = null
  popupLog.value = null
}

async function cancelPopup() {
  if (!popupLogId.value || cancelling.value) return
  cancelling.value = true
  try {
    const res = await agentsApi.cancelRunLog(popupLogId.value)
    popupLog.value = res.data
    if (popupPollTimer) { clearInterval(popupPollTimer); popupPollTimer = null }
  } catch {
    toast.error('Не удалось остановить')
  } finally {
    cancelling.value = false
  }
}

async function sendMessage() {
  if (!inputText.value.trim() || sending.value) return
  const text = inputText.value.trim()
  inputText.value = ''
  sending.value = true
  try {
    const res = await chatApi.sendMessage(props.agentId, text, selectedModel.value || undefined, apiKey.value || undefined, selectedProvider.value || undefined)
    messages.value.push(...res.data.messages)
    lastEnergySpent.value = res.data.energy_spent
    currentEnergyLeft.value = res.data.energy_left
    subStore.setEnergyLeft(res.data.energy_left)
    emit('energy-updated', res.data.energy_left)

    // Автоматически открываем попап если был вызван инструмент
    const toolMsg = res.data.messages.find(m => m.role === 'tool' && m.log_id)
    if (toolMsg) openLogPopup(toolMsg.log_id)

    // Оповещаем родителя об изменениях
    if (toolMsg) emit('tool-run')
    if (res.data.trigger_created) emit('trigger-created')

    // Проверяем системные действия (сохранение настроек)
    const systemMsg = res.data.messages.find(m => m.role === 'tool' && !m.log_id && m.tool_name?.includes('Сохранение'))
    if (systemMsg) emit('settings-saved')
    await scrollToBottom()
  } catch (e) {
    if (e.response?.data?.detail === 'insufficient_balance') {
      showBalancePopup.value = true
    } else {
      toast.error(e.response?.data?.detail || 'Ошибка отправки сообщения')
    }
  } finally {
    sending.value = false
  }
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text, { breaks: true, gfm: true })
}

async function scrollToBottom() {
  await nextTick()
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
}
</script>

<style>
.prose p { margin: 0 0 0.5em; }
.prose p:last-child { margin-bottom: 0; }
.prose ul { list-style: disc; padding-left: 1.25em; margin: 0.4em 0; }
.prose ol { list-style: decimal; padding-left: 1.25em; margin: 0.4em 0; }
.prose li { margin: 0.15em 0; }
.prose strong { font-weight: 600; }
.prose em { font-style: italic; }
.prose code { background: #f3f4f6; border-radius: 4px; padding: 0.1em 0.3em; font-size: 0.85em; font-family: monospace; }
.prose pre { background: #f3f4f6; border-radius: 8px; padding: 0.75em 1em; overflow-x: auto; margin: 0.5em 0; }
.prose pre code { background: none; padding: 0; }
.prose h1, .prose h2, .prose h3 { font-weight: 600; margin: 0.6em 0 0.3em; }
.prose h1 { font-size: 1.1em; }
.prose h2 { font-size: 1.05em; }
.prose h3 { font-size: 1em; }
</style>
