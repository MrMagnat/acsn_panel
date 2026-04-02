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
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { marked } from 'marked'
import { chatApi } from '@/api/chat'
import { agentsApi } from '@/api/agents'
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
const selectedModel = ref(localStorage.getItem(`chat_model_${props.agentId}`) || '')
const apiKey = ref(localStorage.getItem(`chat_key_${props.agentId}`) || '')
const showKey = ref(false)

// Попап результата
const popupLogId = ref(null)
const popupLog = ref(null)
const popupToolName = ref('')
const cancelling = ref(false)
let popupPollTimer = null

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
    const res = await chatApi.sendMessage(props.agentId, text, selectedModel.value || undefined, apiKey.value || undefined)
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
    toast.error(e.response?.data?.detail || 'Ошибка отправки сообщения')
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
