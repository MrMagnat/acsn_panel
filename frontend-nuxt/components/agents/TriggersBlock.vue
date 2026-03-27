<template>
  <div class="space-y-3">
    <div
      v-for="trigger in triggers"
      :key="trigger.id"
      class="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100"
    >
      <div class="text-sm">
        <span class="font-medium text-gray-800">{{ getToolName(trigger.tool_id) }}</span>
        <span class="text-gray-400 mx-2">·</span>
        <span class="text-gray-500 text-xs">{{ cronToLabel(trigger.cron_expr) }}</span>
        <span class="text-gray-400 mx-1">·</span>
        <span class="text-gray-400 text-xs">{{ tzShort(trigger.timezone) }}</span>
        <div v-if="!isToolConfigured(trigger.tool_id)" class="text-xs text-orange-500 mt-0.5">
          ⚠ Инструмент не настроен — автозапуск не выполнится
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="!isToolConfigured(trigger.tool_id)" class="badge-inactive">Не настроен</span>
        <span v-else :class="trigger.is_active ? 'badge-active' : 'badge-inactive'">
          {{ trigger.is_active ? 'Активен' : 'Выключен' }}
        </span>
        <button class="text-gray-300 hover:text-red-400 transition-colors" @click="deleteTrigger(trigger.id)">✕</button>
      </div>
    </div>

    <form v-if="showForm" @submit.prevent="createTrigger" class="p-4 rounded-lg border border-primary-200 bg-primary-50 space-y-3">

      <div>
        <label class="label text-xs">Инструмент</label>
        <select v-model="form.tool_id" class="input text-sm" required>
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
            <option value="Asia/Yakutsk">Якутск (UTC+9)</option>
            <option value="Asia/Vladivostok">Владивосток (UTC+10)</option>
            <option value="Asia/Magadan">Магадан (UTC+11)</option>
            <option value="Asia/Kamchatka">Камчатка (UTC+12)</option>
          </optgroup>
          <optgroup label="СНГ">
            <option value="Europe/Kiev">Киев (UTC+2/3)</option>
            <option value="Europe/Minsk">Минск (UTC+3)</option>
            <option value="Asia/Almaty">Алматы (UTC+5)</option>
            <option value="Asia/Tashkent">Ташкент (UTC+5)</option>
            <option value="Asia/Baku">Баку (UTC+4)</option>
            <option value="Asia/Tbilisi">Тбилиси (UTC+4)</option>
          </optgroup>
          <optgroup label="Европа">
            <option value="Europe/London">Лондон (UTC+0/1)</option>
            <option value="Europe/Paris">Париж, Берлин (UTC+1/2)</option>
            <option value="Europe/Helsinki">Хельсинки (UTC+2/3)</option>
          </optgroup>
          <optgroup label="США">
            <option value="America/New_York">Нью-Йорк (UTC-5/4)</option>
            <option value="America/Chicago">Чикаго (UTC-6/5)</option>
            <option value="America/Los_Angeles">Лос-Анджелес (UTC-8/7)</option>
          </optgroup>
          <optgroup label="Другие">
            <option value="UTC">UTC</option>
            <option value="Asia/Dubai">Дубай (UTC+4)</option>
            <option value="Asia/Tokyo">Токио (UTC+9)</option>
          </optgroup>
        </select>
      </div>

      <div>
        <label class="label text-xs">Расписание</label>
        <div class="flex gap-2 mb-2">
          <button
            type="button"
            class="flex-1 py-2 text-xs rounded-lg border transition-colors"
            :class="scheduleType === 'interval' ? 'border-primary-400 bg-white text-primary-700 font-medium' : 'border-gray-200 bg-white text-gray-500'"
            @click="scheduleType = 'interval'"
          >
            🔁 Каждые N часов/минут
          </button>
          <button
            type="button"
            class="flex-1 py-2 text-xs rounded-lg border transition-colors"
            :class="scheduleType === 'daily' ? 'border-primary-400 bg-white text-primary-700 font-medium' : 'border-gray-200 bg-white text-gray-500'"
            @click="scheduleType = 'daily'"
          >
            🕐 В определённое время
          </button>
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
          <input
            v-model="form.dailyTime"
            type="time"
            class="input text-sm w-32"
            required
          />
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
import { triggersApi } from '~/api/triggers'
import { useToastStore } from '~/stores/toast'

const props = defineProps({ agent: { type: Object, required: true } })

const toast = useToastStore()
const triggers = ref([...(props.agent.auto_triggers || [])])
const showForm = ref(false)
const saving = ref(false)
const scheduleType = ref('interval')

const form = ref({ tool_id: '', interval: '0 * * * *', dailyTime: '09:00', timezone: 'Europe/Moscow' })

const CRON_LABELS = {
  '*/30 * * * *': 'Каждые 30 минут',
  '0 * * * *': 'Каждый час',
  '0 */2 * * *': 'Каждые 2 часа',
  '0 */3 * * *': 'Каждые 3 часа',
  '0 */4 * * *': 'Каждые 4 часа',
  '0 */6 * * *': 'Каждые 6 часов',
  '0 */12 * * *': 'Каждые 12 часов',
  '0 0 * * *': 'Каждый день в 00:00',
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

function tzShort(tz) {
  if (!tz || tz === 'UTC') return 'UTC'
  return tz.split('/').pop().replace(/_/g, ' ')
}

function isToolConfigured(toolId) {
  const at = props.agent.agent_tools.find((t) => t.tool_id === toolId)
  return at?.is_configured ?? true
}

const selectedToolNotConfigured = computed(() => {
  if (!form.value.tool_id) return false
  return !isToolConfigured(form.value.tool_id)
})

function buildCron() {
  if (scheduleType.value === 'interval') return form.value.interval
  const [hh, mm] = form.value.dailyTime.split(':')
  return `${parseInt(mm)} ${parseInt(hh)} * * *`
}

async function createTrigger() {
  saving.value = true
  try {
    const res = await triggersApi.create({
      agent_id: props.agent.id,
      tool_id: form.value.tool_id,
      cron_expr: buildCron(),
      timezone: form.value.timezone,
    })
    triggers.value.push(res.data)
    form.value = { tool_id: '', interval: '0 * * * *', dailyTime: '09:00', timezone: 'Europe/Moscow' }
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
