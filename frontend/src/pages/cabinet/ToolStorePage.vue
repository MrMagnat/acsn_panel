<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold text-gray-900 mb-2">Готовые инструменты</h1>
    <p class="text-gray-500 text-sm mb-6">Воркфлоу-инструменты доступные для добавления вашим агентам</p>

    <div v-if="toolsStore.loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <div v-else id="tools-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="tool in toolsStore.tools"
        :key="tool.id"
        class="card p-5 flex flex-col gap-2"
      >
        <div class="flex items-start justify-between">
          <h3 class="font-semibold text-gray-900">{{ tool.name }}</h3>
          <span class="badge-active text-xs">Активен</span>
        </div>
        <p class="text-sm text-gray-500 flex-1">{{ tool.description || 'Без описания' }}</p>
        <div class="flex items-center justify-between mt-2 pt-2 border-t border-gray-50">
          <span class="text-xs text-gray-400">⚡ {{ tool.energy_cost }} за вызов</span>
          <span class="text-xs text-gray-400">{{ tool.fields?.length ?? 0 }} полей</span>
        </div>
        <button
          class="mt-1 w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-primary-100 text-primary-700 hover:bg-primary-200 transition-colors"
          @click="openRunModal(tool)"
        >
          ▶ Запустить
        </button>
      </div>
    </div>

    <div v-if="!toolsStore.loading && toolsStore.tools.length === 0" class="text-center py-16 text-gray-400">
      Инструменты ещё не добавлены администратором
    </div>

    <!-- Попап: форма запуска -->
    <Teleport to="body">
      <div v-if="runModal" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="closeRunModal">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md flex flex-col overflow-hidden">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <div>
              <h3 class="font-semibold text-gray-900">{{ runModal.name }}</h3>
              <p class="text-xs text-gray-400 mt-0.5">{{ runModal.description }}</p>
            </div>
            <button class="text-gray-400 hover:text-gray-600 text-xl leading-none" @click="closeRunModal">✕</button>
          </div>
          <div class="px-6 py-5 space-y-4 overflow-y-auto" style="max-height: 60vh">
            <div v-if="!runModal.fields?.length" class="text-sm text-gray-400 text-center py-4">
              Этот инструмент не требует настройки. Нажмите «Запустить» ниже.
            </div>
            <div v-for="field in runModal.fields" :key="field.id">
              <label class="label">
                {{ field.field_name }}
                <span v-if="field.required" class="text-red-500 ml-0.5">*</span>
              </label>
              <!-- select -->
              <select v-if="field.field_type === 'select'" v-model="runFields[field.field_name]" class="input">
                <option value="">— выберите —</option>
                <option v-for="opt in parseOptions(field.options)" :key="opt" :value="opt">{{ opt }}</option>
              </select>
              <!-- json -->
              <textarea v-else-if="field.field_type === 'json'" v-model="runFields[field.field_name]"
                class="input resize-none h-24 font-mono text-xs"
                :placeholder="field.hint || '{ key: value }'"></textarea>
              <!-- array -->
              <div v-else-if="field.field_type === 'array'">
                <textarea
                  v-model="runFields[field.field_name]"
                  class="input resize-none h-28 font-mono text-xs"
                  :placeholder="field.hint || 'Один элемент на строку:\nэлемент1\nэлемент2\nэлемент3'"
                ></textarea>
                <p class="text-xs text-gray-400 mt-1">Каждая строка — отдельный элемент массива</p>
              </div>
              <!-- ai_token — ИИ оператор -->
              <div v-else-if="field.field_type === 'ai_token'" class="space-y-3">
                <div class="flex gap-2">
                  <button
                    class="flex-1 py-2 text-xs rounded-lg border transition-colors"
                    :class="(aiTokenSelections[field.field_name]?.mode || 'ascn') === 'ascn' ? 'border-orange-400 bg-orange-50 text-orange-700 font-medium' : 'border-gray-200 text-gray-500'"
                    @click="setAiTokenMode(field.field_name, 'ascn')"
                  >✦ ASCN (встроенный)</button>
                  <button
                    class="flex-1 py-2 text-xs rounded-lg border transition-colors"
                    :class="aiTokenSelections[field.field_name]?.mode === 'own' ? 'border-primary-400 bg-primary-50 text-primary-700 font-medium' : 'border-gray-200 text-gray-500'"
                    @click="setAiTokenMode(field.field_name, 'own')"
                  >🔑 Свой ключ</button>
                </div>
                <!-- ASCN mode -->
                <div v-if="(aiTokenSelections[field.field_name]?.mode || 'ascn') === 'ascn'">
                  <select
                    class="input"
                    v-model="aiTokenSelections[field.field_name].model"
                  >
                    <option value="">— выберите модель —</option>
                    <option v-for="m in ascnModels" :key="m.id" :value="m.id">
                      {{ m.name }} · ${{ (m.price_usd / 100).toFixed(2) }}/сообщ.
                    </option>
                  </select>
                  <p class="text-xs text-gray-400 mt-1">Баланс: <span :class="subStore.balanceUsd > 0 ? 'text-green-600' : 'text-red-500'">{{ subStore.balanceFormatted }}</span></p>
                </div>
                <!-- Own key mode -->
                <div v-else class="space-y-2">
                  <input
                    v-model="aiTokenSelections[field.field_name].operator"
                    class="input text-xs"
                    placeholder="Оператор (напр. openrouter)"
                  />
                  <input
                    v-model="aiTokenSelections[field.field_name].model"
                    class="input text-xs"
                    placeholder="Модель (напр. openai/gpt-4o-mini)"
                  />
                  <input
                    v-model="aiTokenSelections[field.field_name].token"
                    class="input text-xs font-mono"
                    placeholder="API ключ (sk-or-...)"
                    type="password"
                  />
                </div>
              </div>
              <!-- base — выбор базы знаний -->
              <div v-else-if="field.field_type === 'base'" class="space-y-2">
                <select
                  class="input"
                  :value="baseSelections[field.field_name]?.kbId || ''"
                  @change="onBaseKbSelect(field.field_name, $event.target.value)"
                >
                  <option value="">— выберите базу знаний —</option>
                  <option v-for="kb in userKbs" :key="kb.id" :value="kb.id">{{ kb.name }}</option>
                </select>
                <div v-if="baseSelections[field.field_name]?.kbId && kbData[baseSelections[field.field_name].kbId]" class="border border-gray-100 rounded-lg p-3 bg-gray-50">
                  <p class="text-xs text-gray-500 mb-2 font-medium">Выберите колонки для отправки:</p>
                  <div class="space-y-1">
                    <label
                      v-for="col in kbData[baseSelections[field.field_name].kbId].fields"
                      :key="col.id"
                      class="flex items-center gap-2 text-sm cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        :value="col.name"
                        v-model="baseSelections[field.field_name].columns"
                        class="w-4 h-4"
                      />
                      {{ col.name }}
                    </label>
                  </div>
                  <p v-if="baseSelections[field.field_name].columns.length" class="text-xs text-green-600 mt-2">
                    → {{ kbData[baseSelections[field.field_name].kbId].records.length }} строк ×
                    {{ baseSelections[field.field_name].columns.length }} колонок
                  </p>
                </div>
              </div>
              <!-- text / url / number -->
              <input v-else
                v-model="runFields[field.field_name]"
                class="input"
                :placeholder="field.hint || field.field_name"
                :type="field.field_type === 'number' ? 'number' : field.field_type === 'url' ? 'url' : 'text'"
              />
              <p v-if="field.hint && !['json','array','base','ai_token'].includes(field.field_type)" class="text-xs text-gray-400 mt-1">{{ field.hint }}</p>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-2">
            <button class="btn-secondary text-sm" @click="closeRunModal">Отмена</button>
            <button class="btn-primary text-sm" :disabled="launching" @click="launchTool">
              {{ launching ? '...' : '▶ Запустить' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Попап: результат -->
      <div v-if="showResult" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="closeResult">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md flex flex-col" style="max-height: 85vh;">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
            <div class="flex items-center gap-2">
              <span v-if="runLog?.status === 'running'" class="inline-block w-4 h-4 border-2 border-primary-400 border-t-transparent rounded-full animate-spin"></span>
              <span v-else-if="runLog?.status === 'success'" class="text-green-500">✅</span>
              <span v-else-if="runLog?.status === 'cancelled'" class="text-gray-400">⏹</span>
              <span v-else class="text-red-500">❌</span>
              <h3 class="font-semibold text-gray-900">{{ resultToolName }}</h3>
            </div>
            <button class="text-gray-400 hover:text-gray-600" @click="closeResult">✕</button>
          </div>

          <div class="px-6 pt-4 pb-1 shrink-0">
            <span class="text-xs font-medium px-2 py-0.5 rounded-full"
              :class="{
                'bg-yellow-100 text-yellow-700': runLog?.status === 'running',
                'bg-green-100 text-green-700': runLog?.status === 'success',
                'bg-red-100 text-red-700': runLog?.status === 'error',
                'bg-gray-100 text-gray-500': runLog?.status === 'cancelled',
              }">
              {{ { running: 'Выполняется...', success: 'Выполнено', error: 'Ошибка', cancelled: 'Остановлено' }[runLog?.status] ?? 'Запускаем...' }}
            </span>
            <span v-if="runLog?.status === 'running'" class="text-xs text-gray-400 ml-2">обновляется каждые 2 сек...</span>
          </div>

          <div class="px-6 py-4 overflow-y-auto flex-1">
            <ResultRenderer v-if="runLog" :result-json="runLog.result_json" :status="runLog.status" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useToolsStore } from '@/stores/tools'
import { toolsApi } from '@/api/tools'
import { agentsApi } from '@/api/agents'
import { kbApi } from '@/api/knowledge-base'
import { useToastStore } from '@/stores/toast'
import { useSubscriptionStore } from '@/stores/subscription'
import ResultRenderer from '@/components/tools/ResultRenderer.vue'

const toolsStore = useToolsStore()
const toast = useToastStore()
const subStore = useSubscriptionStore()

const runModal = ref(null)
const runFields = reactive({})
const launching = ref(false)

// Base knowledge fields
const userKbs = ref([])
const baseSelections = reactive({})  // { [fieldName]: { kbId, columns: [] } }
const kbData = reactive({})          // { [kbId]: { fields: [], records: [] } }

// AI token fields
const ascnModels = ref([])
const aiTokenSelections = reactive({})  // { [fieldName]: { mode, model, operator, token } }

const showResult = ref(false)
const runLog = ref(null)
const resultToolName = ref('')
const cancelling = ref(false)
let currentLogId = null
let pollTimer = null

onMounted(async () => {
  toolsStore.fetchTools()
  try {
    const res = await import('@/api/http').then(m => m.default.get('/onboarding/ascn-models'))
    ascnModels.value = res.data
  } catch { /**/ }
})
onUnmounted(stopPolling)

function parseOptions(options) {
  if (!options) return []
  try { return JSON.parse(options) } catch { return [] }
}

function setAiTokenMode(fieldName, mode) {
  aiTokenSelections[fieldName] = { mode, model: '', operator: 'openrouter', token: '' }
}

async function openRunModal(tool) {
  runModal.value = tool
  Object.keys(runFields).forEach(k => delete runFields[k])
  Object.keys(baseSelections).forEach(k => delete baseSelections[k])
  Object.keys(aiTokenSelections).forEach(k => delete aiTokenSelections[k])
  if (tool.fields) {
    tool.fields.forEach(f => {
      if (f.field_type === 'base') {
        baseSelections[f.field_name] = { kbId: '', columns: [] }
      } else if (f.field_type === 'ai_token') {
        aiTokenSelections[f.field_name] = { mode: 'ascn', model: '', operator: 'openrouter', token: '' }
      } else {
        runFields[f.field_name] = ''
      }
    })
  }
  // Загружаем список баз если есть base-поля
  const hasBase = tool.fields?.some(f => f.field_type === 'base')
  if (hasBase && !userKbs.value.length) {
    try {
      const res = await kbApi.list()
      userKbs.value = res.data
    } catch { /**/ }
  }
}

async function onBaseKbSelect(fieldName, kbId) {
  baseSelections[fieldName].kbId = kbId
  baseSelections[fieldName].columns = []
  if (kbId && !kbData[kbId]) {
    try {
      const res = await kbApi.get(kbId)
      kbData[kbId] = res.data
    } catch { /**/ }
  }
}

function closeRunModal() {
  runModal.value = null
}

async function launchTool() {
  if (launching.value) return
  launching.value = true
  const tool = runModal.value
  try {
    // Собираем финальные значения
    const fieldValues = { ...runFields }

    for (const field of (tool.fields || [])) {
      if (field.field_type === 'array') {
        const raw = runFields[field.field_name] || ''
        fieldValues[field.field_name] = raw.split('\n').map(s => s.trim()).filter(Boolean)
      } else if (field.field_type === 'ai_token') {
        const sel = aiTokenSelections[field.field_name]
        if (!sel?.model) {
          toast.error(`Выберите модель для поля «${field.field_name}»`)
          launching.value = false
          return
        }
        if (sel.mode === 'ascn') {
          fieldValues[field.field_name] = { operator: 'ascn', model: sel.model, token: '__ascn__' }
        } else {
          if (!sel.token) {
            toast.error(`Введите API ключ для поля «${field.field_name}»`)
            launching.value = false
            return
          }
          fieldValues[field.field_name] = { operator: sel.operator, model: sel.model, token: sel.token }
        }
      } else if (field.field_type === 'base') {
        const sel = baseSelections[field.field_name]
        if (!sel?.kbId) {
          toast.error(`Выберите базу знаний для поля «${field.field_name}»`)
          launching.value = false
          return
        }
        if (!sel.columns.length) {
          toast.error(`Выберите хотя бы одну колонку для поля «${field.field_name}»`)
          launching.value = false
          return
        }
        const kb = kbData[sel.kbId]
        fieldValues[field.field_name] = kb.records.map(r =>
          sel.columns.map(col => r.data[col] ?? '')
        )
      }
    }

    const res = await toolsApi.runStandalone(tool.id, fieldValues)
    if (res.data.energy_left !== undefined) subStore.setEnergyLeft(res.data.energy_left)

    resultToolName.value = tool.name
    closeRunModal()
    showResult.value = true
    runLog.value = null
    currentLogId = res.data.log_id
    await pollLog(currentLogId)
    if (runLog.value?.status === 'running') {
      pollTimer = setInterval(() => pollLog(currentLogId), 2000)
    }
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка запуска')
  } finally {
    launching.value = false
  }
}

async function pollLog(logId) {
  try {
    const res = await agentsApi.pollRunLog(logId)
    runLog.value = res.data
    if (res.data.status !== 'running') stopPolling()
  } catch { stopPolling() }
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
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

function closeResult() {
  stopPolling()
  showResult.value = false
  runLog.value = null
  currentLogId = null
}
</script>
