<template>
  <div class="space-y-3">
    <!-- Список триггеров -->
    <div
      v-for="trigger in triggers"
      :key="trigger.id"
      class="rounded-lg border border-gray-100 bg-gray-50 overflow-hidden"
    >
      <!-- Шапка карточки -->
      <div class="flex items-start justify-between p-3">
        <div class="text-sm min-w-0">
          <div class="font-medium text-gray-800">{{ getToolName(trigger.tool_id) }}</div>
          <div class="flex items-center gap-1.5 mt-0.5 flex-wrap">
            <span class="text-gray-400 text-xs">{{ cronToLabel(trigger.cron_expr) }}</span>
            <span class="text-gray-300">·</span>
            <span class="text-gray-400 text-xs">{{ tzShort(trigger.timezone) }}</span>
          </div>
          <!-- Сводка сохранённых данных -->
          <div v-if="inputDataSummary(trigger)" class="mt-1 text-xs text-primary-600 bg-primary-50 rounded px-2 py-0.5 inline-block">
            📋 {{ inputDataSummary(trigger) }}
          </div>
          <div v-if="!isToolConfigured(trigger.tool_id)" class="text-xs text-orange-500 mt-0.5">
            ⚠ Инструмент не настроен
          </div>
        </div>
        <div class="flex items-center gap-1.5 shrink-0 ml-2">
          <span v-if="!isToolConfigured(trigger.tool_id)" class="badge-inactive">Не настроен</span>
          <span v-else :class="trigger.is_active ? 'badge-active' : 'badge-inactive'">
            {{ trigger.is_active ? 'Активен' : 'Выкл' }}
          </span>
          <button
            class="text-xs px-2 py-1 rounded-lg border border-gray-200 text-gray-500 hover:bg-white hover:border-primary-300 hover:text-primary-600 transition-colors"
            @click="startEdit(trigger)"
          >✎</button>
          <button class="text-gray-300 hover:text-red-400 transition-colors text-sm" @click="deleteTrigger(trigger.id)">✕</button>
        </div>
      </div>

      <!-- Форма редактирования (раскрывается inline) -->
      <div v-if="editingId === trigger.id" class="border-t border-gray-200 p-3 bg-white space-y-3">
        <div class="text-xs font-medium text-gray-500 mb-1">Данные для этого автозапуска:</div>

        <!-- Поля инструмента -->
        <div v-for="field in getToolFields(trigger.tool_id)" :key="field.id">
          <label class="text-xs text-gray-600 mb-0.5 block">
            {{ field.field_name }}
            <span v-if="field.required" class="text-red-500">*</span>
          </label>
          <select v-if="field.field_type === 'select'" v-model="editData[field.field_name]" class="input text-sm">
            <option value="">— выберите —</option>
            <option v-for="opt in parseOptions(field.options)" :key="opt" :value="opt">{{ opt }}</option>
          </select>
          <textarea
            v-else-if="field.field_type === 'textarea' || field.field_type === 'json' || field.field_type === 'array'"
            v-model="editData[field.field_name]"
            class="input resize-none text-sm font-mono"
            rows="3"
            :placeholder="field.hint || ''"
          />
          <input
            v-else-if="field.field_type !== 'ai_token'"
            v-model="editData[field.field_name]"
            class="input text-sm"
            :placeholder="field.hint || ''"
          />
        </div>

        <!-- Расписание + часовой пояс -->
        <div class="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100">
          <div>
            <label class="text-xs text-gray-600 mb-0.5 block">Расписание</label>
            <select v-model="editCron" class="input text-sm">
              <option v-for="(label, val) in CRON_OPTIONS" :key="val" :value="val">{{ label }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-gray-600 mb-0.5 block">Часовой пояс</label>
            <select v-model="editTimezone" class="input text-sm">
              <option value="Europe/Moscow">Москва (UTC+3)</option>
              <option value="Europe/Kaliningrad">Калининград (UTC+2)</option>
              <option value="Asia/Yekaterinburg">Екатеринбург (UTC+5)</option>
              <option value="Asia/Novosibirsk">Новосибирск (UTC+7)</option>
              <option value="Asia/Vladivostok">Владивосток (UTC+10)</option>
              <option value="Europe/Kiev">Киев (UTC+2/3)</option>
              <option value="Europe/Minsk">Минск (UTC+3)</option>
              <option value="UTC">UTC</option>
              <option value="Europe/London">Лондон (UTC+0/1)</option>
              <option value="Europe/Paris">Париж (UTC+1/2)</option>
              <option value="America/New_York">Нью-Йорк (UTC-5)</option>
              <option value="America/Los_Angeles">Лос-Анджелес (UTC-8)</option>
            </select>
          </div>
        </div>

        <div class="flex gap-2 pt-1">
          <button class="btn-secondary text-xs" @click="editingId = null">Отмена</button>
          <button class="btn-primary text-xs" :disabled="saving" @click="saveEdit(trigger)">
            {{ saving ? 'Сохраняю...' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Форма добавления нового триггера -->
    <form v-if="showForm" @submit.prevent="createTrigger" class="p-4 rounded-lg border border-primary-200 bg-primary-50 space-y-3">

      <!-- Выбор инструмента -->
      <div>
        <label class="label text-xs">Инструмент</label>
        <select v-model="form.tool_id" class="input text-sm" required @change="onToolChange">
          <option value="">Выберите инструмент...</option>
          <option
            v-for="at in props.agent.agent_tools"
            :key="at.tool_id"
            :value="at.tool_id"
            :disabled="!at.is_configured"
          >
            {{ at.tool?.name ?? at.tool_id }}{{ !at.is_configured ? ' — не настроен' : '' }}
          </option>
        </select>
        <p v-if="props.agent.agent_tools.length === 0" class="text-xs text-yellow-600 mt-1">
          Сначала добавьте инструменты агенту
        </p>
        <p v-else-if="selectedToolNotConfigured" class="text-xs text-red-500 mt-1">
          Настройте инструмент перед созданием автозапуска
        </p>
      </div>

      <!-- Поля инструмента (данные для этого запуска) -->
      <div v-if="form.tool_id && selectedToolFields.length" class="space-y-2 pt-1 border-t border-primary-200">
        <div class="text-xs font-medium text-primary-700">Данные для этого автозапуска:</div>
        <div v-for="field in selectedToolFields" :key="field.id">
          <label class="text-xs text-gray-600 mb-0.5 block">
            {{ field.field_name }}
            <span v-if="field.required" class="text-red-500">*</span>
          </label>
          <select v-if="field.field_type === 'select'" v-model="form.input_data[field.field_name]" class="input text-sm">
            <option value="">— выберите —</option>
            <option v-for="opt in parseOptions(field.options)" :key="opt" :value="opt">{{ opt }}</option>
          </select>
          <textarea
            v-else-if="field.field_type === 'textarea' || field.field_type === 'json' || field.field_type === 'array'"
            v-model="form.input_data[field.field_name]"
            class="input resize-none text-sm font-mono"
            rows="3"
            :placeholder="field.hint || ''"
          />
          <input
            v-else-if="field.field_type !== 'ai_token'"
            v-model="form.input_data[field.field_name]"
            class="input text-sm"
            :placeholder="field.hint || ''"
          />
        </div>
      </div>

      <!-- Часовой пояс -->
      <div>
        <label class="label text-xs">Часовой пояс</label>
        <select v-model="form.timezone" class="input text-sm">
          <optgroup label="Россия">
            <option value="Europe/Kaliningrad">Калининград (UTC+2)</option>
            <option value="Europe/Moscow">Москва, Санкт-Петербург (UTC+3)</option>
            <option value="Europe/Samara">Самара, Ижевск (UTC+4)</option>
            <option value="Asia/Yekaterinburg">Екатеринбург (UTC+5)</option>
            <option value="Asia/Omsk">Омск (UTC+6)</option>
            <option value="Asia/Krasnoyarsk">Красноярск (UTC+7)</option>
            <option value="Asia/Irkutsk">Иркутск (UTC+8)</option>
            <option value="Asia/Vladivostok">Владивосток (UTC+10)</option>
          </optgroup>
          <optgroup label="СНГ">
            <option value="Europe/Kiev">Киев (UTC+2/3)</option>
            <option value="Europe/Minsk">Минск (UTC+3)</option>
            <option value="Asia/Almaty">Алматы (UTC+5)</option>
            <option value="Asia/Tashkent">Ташкент (UTC+5)</option>
          </optgroup>
          <optgroup label="Европа / Мир">
            <option value="Europe/London">Лондон (UTC+0/1)</option>
            <option value="Europe/Paris">Париж, Берлин (UTC+1/2)</option>
            <option value="America/New_York">Нью-Йорк (UTC-5/4)</option>
            <option value="America/Los_Angeles">Лос-Анджелес (UTC-8/7)</option>
            <option value="UTC">UTC</option>
          </optgroup>
        </select>
      </div>

      <!-- Расписание -->
      <div>
        <label class="label text-xs">Расписание</label>
        <div class="flex gap-2 mb-2">
          <button
            type="button"
            class="flex-1 py-2 text-xs rounded-lg border transition-colors"
            :class="scheduleType === 'interval' ? 'border-primary-400 bg-white text-primary-700 font-medium' : 'border-gray-200 bg-white text-gray-500'"
            @click="scheduleType = 'interval'"
          >🔁 Каждые N часов/минут</button>
          <button
            type="button"
            class="flex-1 py-2 text-xs rounded-lg border transition-colors"
            :class="scheduleType === 'daily' ? 'border-primary-400 bg-white text-primary-700 font-medium' : 'border-gray-200 bg-white text-gray-500'"
            @click="scheduleType = 'daily'"
          >🕐 В определённое время</button>
        </div>
        <select v-if="scheduleType === 'interval'" v-model="form.interval" class="input text-sm">
          <option value="*/30 * * * *">Каждые 30 минут</option>
          <option value="0 * * * *">Каждый час</option>
          <option value="0 */2 * * *">Каждые 2 часа</option>
          <option value="0 */3 * * *">Каждые 3 часа</option>
          <option value="0 */4 * * *">Каждые 4 часа</option>
          <option value="0 */6 * * *">Каждые 6 часов</option>
          <option value="0 */12 * * *">Каждые 12 часов</option>
          <option value="0 0 * * *">Раз в сутки (в полночь)</option>
        </select>
        <div v-else class="flex items-center gap-2">
          <span class="text-sm text-gray-500">Каждый день в</span>
          <input v-model="form.dailyTime" type="time" class="input text-sm w-32" required />
        </div>
      </div>

      <div class="flex gap-2">
        <button type="button" class="btn-secondary text-xs" @click="showForm = false">Отмена</button>
        <button type="submit" class="btn-primary text-xs" :disabled="saving || !form.tool_id || selectedToolNotConfigured">
          {{ saving ? 'Создаю...' : 'Создать' }}
        </button>
      </div>
    </form>

    <button v-if="!showForm" class="text-sm text-primary-600 hover:underline" @click="showForm = true">
      + Добавить автозапуск
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { triggersApi } from '@/api/triggers'
import { useToastStore } from '@/stores/toast'

const props = defineProps({ agent: { type: Object, required: true } })

const toast = useToastStore()
const triggers = ref([...(props.agent.auto_triggers || [])])
const showForm = ref(false)
const saving = ref(false)
const scheduleType = ref('interval')

// Состояние редактирования
const editingId = ref(null)
const editData = ref({})
const editCron = ref('0 * * * *')
const editTimezone = ref('Europe/Moscow')

const form = ref({
  tool_id: '',
  interval: '0 * * * *',
  dailyTime: '09:00',
  timezone: 'Europe/Moscow',
  input_data: {},
})

const CRON_OPTIONS = {
  '*/30 * * * *': 'Каждые 30 минут',
  '0 * * * *': 'Каждый час',
  '0 */2 * * *': 'Каждые 2 часа',
  '0 */4 * * *': 'Каждые 4 часа',
  '0 */6 * * *': 'Каждые 6 часов',
  '0 */12 * * *': 'Каждые 12 часов',
  '0 0 * * *': 'Раз в сутки (полночь)',
}

const CRON_LABELS = {
  ...CRON_OPTIONS,
}

function cronToLabel(cron) {
  if (CRON_LABELS[cron]) return CRON_LABELS[cron]
  const m = cron.match(/^(\d+) (\d+) \* \* \*$/)
  if (m) return `Каждый день в ${m[2].padStart(2, '0')}:${m[1].padStart(2, '0')}`
  return cron
}

function getToolName(toolId) {
  const at = props.agent.agent_tools.find((t) => t.tool_id === toolId)
  return at?.tool?.name ?? toolId
}

function getToolFields(toolId) {
  const at = props.agent.agent_tools.find((t) => t.tool_id === toolId)
  return at?.tool?.fields ?? []
}

function getToolFieldValues(toolId) {
  const at = props.agent.agent_tools.find((t) => t.tool_id === toolId)
  return at?.field_values ?? {}
}

function tzShort(tz) {
  if (!tz || tz === 'UTC') return 'UTC'
  return tz.split('/').pop().replace(/_/g, ' ')
}

function isToolConfigured(toolId) {
  const at = props.agent.agent_tools.find((t) => t.tool_id === toolId)
  return at?.is_configured ?? true
}

function parseOptions(opts) {
  if (!opts) return []
  if (Array.isArray(opts)) return opts
  return String(opts).split('\n').map((s) => s.trim()).filter(Boolean)
}

// Сводка сохранённых данных
function inputDataSummary(trigger) {
  const data = trigger.input_data || {}
  const filled = Object.entries(data).filter(([, v]) => v !== '' && v !== null && v !== undefined)
  if (!filled.length) return null
  if (filled.length === 1) {
    const [, v] = filled[0]
    const str = String(v)
    return str.length > 40 ? str.slice(0, 40) + '…' : str
  }
  return `${filled.length} параметров сохранено`
}

const selectedToolFields = computed(() => getToolFields(form.value.tool_id))

const selectedToolNotConfigured = computed(() => {
  if (!form.value.tool_id) return false
  return !isToolConfigured(form.value.tool_id)
})

// При выборе инструмента — предзаполняем из field_values
function onToolChange() {
  const base = getToolFieldValues(form.value.tool_id)
  form.value.input_data = { ...base }
}

function buildCron() {
  if (scheduleType.value === 'interval') return form.value.interval
  const [hh, mm] = form.value.dailyTime.split(':')
  return `${parseInt(mm)} ${parseInt(hh)} * * *`
}

// Открыть редактирование триггера
function startEdit(trigger) {
  if (editingId.value === trigger.id) {
    editingId.value = null
    return
  }
  editingId.value = trigger.id
  const baseValues = getToolFieldValues(trigger.tool_id)
  editData.value = { ...baseValues, ...(trigger.input_data || {}) }
  editCron.value = trigger.cron_expr in CRON_OPTIONS ? trigger.cron_expr : '0 * * * *'
  editTimezone.value = trigger.timezone || 'Europe/Moscow'
}

async function saveEdit(trigger) {
  saving.value = true
  try {
    const res = await triggersApi.update(trigger.id, {
      cron_expr: editCron.value,
      timezone: editTimezone.value,
      input_data: editData.value,
    })
    const idx = triggers.value.findIndex((t) => t.id === trigger.id)
    if (idx !== -1) triggers.value[idx] = res.data
    editingId.value = null
    toast.success('Автозапуск обновлён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка обновления')
  } finally {
    saving.value = false
  }
}

async function createTrigger() {
  saving.value = true
  try {
    const res = await triggersApi.create({
      agent_id: props.agent.id,
      tool_id: form.value.tool_id,
      cron_expr: buildCron(),
      timezone: form.value.timezone,
      input_data: form.value.input_data,
    })
    triggers.value.push(res.data)
    form.value = { tool_id: '', interval: '0 * * * *', dailyTime: '09:00', timezone: 'Europe/Moscow', input_data: {} }
    showForm.value = false
    toast.success('Автозапуск создан')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка создания триггера')
  } finally {
    saving.value = false
  }
}

async function deleteTrigger(id) {
  try {
    await triggersApi.delete(id)
    triggers.value = triggers.value.filter((t) => t.id !== id)
    toast.success('Автозапуск удалён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка удаления')
  }
}
</script>
