<template>
  <!-- Плитка инструмента -->
  <div class="card p-4 flex items-center justify-between gap-3">
    <!-- Левая часть — клик открывает настройки -->
    <div class="flex items-center gap-3 min-w-0 cursor-pointer flex-1" @click="openModal = true">
      <div class="w-9 h-9 rounded-lg bg-primary-50 flex items-center justify-center text-lg shrink-0">🔧</div>
      <div class="min-w-0">
        <div class="font-medium text-sm text-gray-900 truncate">{{ agentTool.tool.name }}</div>
        <span :class="agentTool.is_configured ? 'badge-active' : 'badge-warning'" class="mt-0.5 inline-block">
          {{ agentTool.is_configured ? 'Настроен' : 'Не активен' }}
        </span>
      </div>
    </div>

    <!-- Правая часть -->
    <div class="flex items-center gap-2 shrink-0">
      <span class="text-xs text-gray-400">⚡{{ agentTool.tool.energy_cost }}</span>

      <!-- Кнопка Запустить -->
      <button
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
        :class="running ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-primary-100 text-primary-700 hover:bg-primary-200'"
        :disabled="running"
        @click.stop="handleRun"
      >
        <span v-if="running" class="inline-block w-3 h-3 border-2 border-primary-400 border-t-transparent rounded-full animate-spin"></span>
        <span v-else>▶</span>
        {{ running ? 'Запуск...' : 'Запустить' }}
      </button>

      <!-- Удалить -->
      <button class="text-gray-300 hover:text-red-400 transition-colors text-lg leading-none" @click.stop="$emit('remove', agentTool.tool_id)">✕</button>
    </div>
  </div>

  <Teleport to="body">
    <!-- Попап настроек -->
    <div v-if="openModal" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="openModal = false">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-md flex flex-col overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h3 class="font-semibold text-gray-900">{{ agentTool.tool.name }}</h3>
            <p class="text-xs text-gray-400 mt-0.5">{{ agentTool.tool.description }}</p>
          </div>
          <button class="text-gray-400 hover:text-gray-600 text-xl leading-none" @click="openModal = false">✕</button>
        </div>
        <div class="px-6 py-5 space-y-4">
          <div v-if="!agentTool.tool.fields?.length" class="text-sm text-gray-400 text-center py-4">
            Этот инструмент не требует настройки
          </div>
          <div v-for="field in agentTool.tool.fields" :key="field.id">
            <label class="label">
              {{ field.field_name }}
              <span v-if="field.required" class="text-red-500 ml-0.5">*</span>
              <span v-if="field.is_runtime" class="ml-1 text-xs text-primary-500 font-normal">💬 чат</span>
            </label>
            <input v-model="localValues[field.field_name]" class="input"
              :placeholder="field.hint || field.field_name"
              :type="field.field_type === 'number' ? 'number' : field.field_type === 'url' ? 'url' : 'text'" />
            <p v-if="field.hint" class="text-xs text-gray-400 mt-1">{{ field.hint }}</p>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-2">
          <button class="btn-secondary text-sm" @click="openModal = false">Закрыть</button>
          <button v-if="agentTool.tool.fields?.length" class="btn-primary text-sm" @click="save">Сохранить</button>
        </div>
      </div>
    </div>

    <!-- Попап: инструмент не настроен -->
    <div v-if="showNotConfigured" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="showNotConfigured = false">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-8 flex flex-col items-center text-center">
        <div class="w-14 h-14 rounded-full bg-yellow-100 flex items-center justify-center text-3xl mb-4">⚙️</div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Сначала настройте инструмент</h3>
        <p class="text-sm text-gray-500 mb-6">Заполните все обязательные поля инструмента «{{ agentTool.tool.name }}», чтобы запустить его.</p>
        <button class="btn-primary w-full py-2.5 text-sm" @click="openSettings">Настроить →</button>
        <button class="text-sm text-gray-400 hover:text-gray-600 mt-3" @click="showNotConfigured = false">Отмена</button>
      </div>
    </div>

    <!-- Попап: результат запуска (с polling) -->
    <div v-if="showResult" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="closeResult">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
        <!-- Шапка -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div class="flex items-center gap-2">
            <span v-if="runLog?.status === 'running'" class="inline-block w-4 h-4 border-2 border-primary-400 border-t-transparent rounded-full animate-spin"></span>
            <span v-else-if="runLog?.status === 'success'" class="text-green-500">✅</span>
            <span v-else-if="runLog?.status === 'cancelled'" class="text-gray-400">⏹</span>
            <span v-else class="text-red-500">❌</span>
            <h3 class="font-semibold text-gray-900">{{ agentTool.tool.name }}</h3>
          </div>
          <button class="text-gray-400 hover:text-gray-600" @click="closeResult">✕</button>
        </div>

        <!-- Статус -->
        <div class="px-6 pt-4 pb-1">
          <span class="text-xs font-medium px-2 py-0.5 rounded-full"
            :class="{
              'bg-yellow-100 text-yellow-700': runLog?.status === 'running',
              'bg-green-100 text-green-700': runLog?.status === 'success',
              'bg-red-100 text-red-700': runLog?.status === 'error',
              'bg-gray-100 text-gray-500': runLog?.status === 'cancelled',
            }">
            {{ statusLabel }}
          </span>
          <span v-if="runLog?.status === 'running'" class="text-xs text-gray-400 ml-2">обновляется каждые 2 сек...</span>
        </div>

        <!-- Результат -->
        <div class="px-6 py-4">
          <ResultRenderer
            v-if="runLog"
            :result-json="runLog.result_json"
            :status="runLog.status"
          />
          <div v-else class="flex items-center gap-2 text-sm text-gray-400 py-4">
            <span class="inline-block w-4 h-4 border-2 border-gray-300 border-t-transparent rounded-full animate-spin"></span>
            Запускаем инструмент...
          </div>
        </div>

        <div class="px-6 pb-4 flex justify-between items-center">
          <button
            v-if="runLog?.status === 'running'"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 transition-colors"
            :disabled="cancelling"
            @click="cancelRun"
          >
            <span v-if="cancelling" class="inline-block w-3 h-3 border-2 border-red-400 border-t-transparent rounded-full animate-spin"></span>
            <span v-else>⏹</span>
            {{ cancelling ? 'Останавливаю...' : 'Остановить' }}
          </button>
          <div v-else></div>
          <button class="btn-secondary text-sm" @click="closeResult">Закрыть</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, watch, computed, onUnmounted } from 'vue'
import { agentsApi } from '@/api/agents'
import { useToastStore } from '@/stores/toast'
import { useSubscriptionStore } from '@/stores/subscription'
import ResultRenderer from './ResultRenderer.vue'

const props = defineProps({
  agentTool: { type: Object, required: true },
  agentId: { type: String, required: true },
})
const emit = defineEmits(['update', 'remove'])

const toast = useToastStore()
const subStore = useSubscriptionStore()
const openModal = ref(false)
const showNotConfigured = ref(false)
const running = ref(false)
const localValues = reactive({ ...props.agentTool.field_values })

// Результат и polling
const showResult = ref(false)
const runLog = ref(null)
const cancelling = ref(false)
let pollTimer = null
let currentLogId = null

watch(() => props.agentTool.field_values, (v) => { Object.assign(localValues, v) })

const statusLabel = computed(() => {
  if (!runLog.value) return 'Запускаем...'
  return { running: 'Выполняется...', success: 'Выполнено', error: 'Ошибка', cancelled: 'Остановлено' }[runLog.value.status] ?? runLog.value.status
})

function save() {
  emit('update', { toolId: props.agentTool.tool_id, fieldValues: { ...localValues } })
  openModal.value = false
}

function handleRun() {
  if (!props.agentTool.is_configured) { showNotConfigured.value = true; return }
  runTool()
}

function openSettings() { showNotConfigured.value = false; openModal.value = true }

function closeResult() {
  stopPolling()
  showResult.value = false
  runLog.value = null
  currentLogId = null
}

async function cancelRun() {
  if (!currentLogId || cancelling.value) return
  cancelling.value = true
  try {
    const res = await agentsApi.cancelRunLog(currentLogId)
    runLog.value = res.data
    stopPolling()
  } catch {
    toast.error('Не удалось остановить процесс')
  } finally {
    cancelling.value = false
  }
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function pollLog(logId) {
  try {
    const res = await agentsApi.pollRunLog(logId)
    runLog.value = res.data
    if (res.data.status !== 'running') stopPolling()
  } catch { stopPolling() }
}

async function runTool() {
  running.value = true
  showResult.value = true
  runLog.value = null

  try {
    const res = await agentsApi.runTool(props.agentId, props.agentTool.tool_id)

    if (res.data.energy_left !== undefined) subStore.setEnergyLeft(res.data.energy_left)

    const logId = res.data.log_id
    if (!logId) {
      // Старый формат — нет лога
      runLog.value = { status: res.data.status === 'ok' ? 'success' : 'error', result_json: JSON.stringify(res.data.result) }
      return
    }

    currentLogId = logId

    // Сразу подгружаем лог
    await pollLog(logId)

    // Если ещё running — запускаем polling каждые 2 сек
    if (runLog.value?.status === 'running') {
      pollTimer = setInterval(() => pollLog(logId), 2000)
    }
  } catch (e) {
    runLog.value = { status: 'error', result_json: JSON.stringify({ error: e.response?.data?.detail || 'Ошибка запуска' }) }
  } finally {
    running.value = false
  }
}

onUnmounted(stopPolling)
</script>
