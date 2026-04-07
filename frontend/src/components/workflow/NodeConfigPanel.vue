<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 shrink-0">
      <div>
        <div class="font-semibold text-sm text-gray-900">
          <span v-if="nodeType === 'trigger'">{{ triggerLabels[nodeData?.triggerType] ?? 'Триггер' }}</span>
          <span v-else-if="nodeType === 'output'">Точка выхода</span>
          <span v-else>{{ agentTool?.tool?.name ?? '—' }}</span>
        </div>
        <div class="text-xs text-gray-400 mt-0.5">
          <span v-if="nodeType === 'trigger'">Начало цепочки</span>
          <span v-else-if="nodeType === 'output'">Конец цепочки</span>
          <span v-else>⚡ {{ agentTool?.tool?.energy_cost ?? 0 }} за запуск</span>
        </div>
      </div>
      <button class="text-gray-400 hover:text-gray-600 text-lg" @click="$emit('close')">✕</button>
    </div>

    <!-- Trigger config -->
    <div v-if="nodeType === 'trigger'" class="flex-1 overflow-y-auto px-4 py-3 space-y-4">
      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block">Тип триггера</label>
        <div class="flex gap-2">
          <button
            v-for="t in [{ v: 'manual', l: '▶ Вручную' }, { v: 'cron', l: '🕐 По расписанию' }]"
            :key="t.v"
            class="flex-1 py-1.5 text-xs rounded-lg border transition-colors"
            :class="triggerLocal.triggerType === t.v ? 'bg-emerald-500 text-white border-emerald-500' : 'border-gray-200 text-gray-600 hover:border-emerald-300'"
            @click="triggerLocal.triggerType = t.v; emitSpecial()"
          >{{ t.l }}</button>
        </div>
      </div>

      <div v-if="triggerLocal.triggerType === 'cron'" class="space-y-3">
        <div>
          <label class="text-xs font-medium text-gray-600 mb-2 block">Частота запуска</label>
          <div class="grid grid-cols-2 gap-1.5 mb-3">
            <button
              v-for="opt in SCHEDULE_PRESETS"
              :key="opt.cron"
              class="py-1.5 px-2 text-xs rounded-lg border transition-colors text-left"
              :class="triggerLocal.schedule === opt.cron ? 'bg-purple-100 border-purple-400 text-purple-700 font-medium' : 'border-gray-200 text-gray-600 hover:border-purple-300'"
              @click="triggerLocal.schedule = opt.cron; triggerLocal.scheduleMode = 'preset'; emitSpecial()"
            >{{ opt.label }}</button>
          </div>
        </div>

        <div>
          <label class="text-xs font-medium text-gray-600 mb-1 block">— или в точное время</label>
          <div class="flex gap-2 items-center">
            <input
              type="time"
              v-model="exactTime"
              class="input text-sm flex-1"
              @change="applyExactTime"
            />
            <select v-model="triggerLocal.timezone" class="input text-xs flex-1" @change="applyExactTime">
              <option v-for="tz in TIMEZONES" :key="tz.v" :value="tz.v">{{ tz.l }}</option>
            </select>
          </div>
          <p class="text-xs text-gray-400 mt-1">Каждый день в указанное время</p>
        </div>

        <div v-if="triggerLocal.schedule" class="text-xs bg-purple-50 rounded-lg px-3 py-2 text-purple-700">
          CRON: <code>{{ triggerLocal.schedule }}</code>
        </div>
      </div>

      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block">Метка (необязательно)</label>
        <input v-model="triggerLocal.label" class="input text-sm" placeholder="Мой триггер" @input="emitSpecial" />
      </div>
    </div>

    <!-- Output config -->
    <div v-else-if="nodeType === 'output'" class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
      <div class="p-3 bg-indigo-50 rounded-xl border border-indigo-100">
        <div class="text-sm font-medium text-indigo-800 mb-1">🏁 Финальная точка</div>
        <p class="text-xs text-indigo-600">
          Все данные, которые придут в эту точку, будут сохранены как результат запуска и отображены в истории.
        </p>
      </div>
      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block">Метка (необязательно)</label>
        <input v-model="outputLocal.label" class="input text-sm" placeholder="Результат" @input="emitSpecial" />
      </div>
    </div>

    <!-- Tool config -->
    <div v-else class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
      <div v-if="!inputFields.length" class="text-sm text-gray-400 text-center py-6">
        У этого инструмента нет настраиваемых полей
      </div>

      <div v-for="field in inputFields" :key="field.field_name">
        <label class="text-xs font-medium text-gray-600 mb-1 flex items-center gap-1">
          {{ field.field_name }}
          <span v-if="field.required" class="text-red-400">*</span>
          <span v-if="field.hint" class="text-gray-400 font-normal">— {{ field.hint }}</span>
        </label>

        <!-- Connected from another node -->
        <div v-if="isConnected(field.field_name)" class="flex items-center gap-2 px-3 py-2 bg-purple-50 rounded-lg border border-purple-200 text-xs text-purple-700">
          <span>🔗</span>
          <span>{{ getConnectionSource(field.field_name) }}</span>
        </div>

        <template v-else>
          <!-- ai_token: provider/model/token selector -->
          <AiTokenField
            v-if="field.field_type === 'ai_token'"
            :model-value="localData[field.field_name]"
            @update:model-value="localData[field.field_name] = $event; emitUpdate()"
          />

          <!-- base: knowledge base -->
          <div v-else-if="field.field_type === 'base'" class="px-3 py-2 bg-green-50 rounded-lg border border-green-100 text-xs text-green-700">
            📚 База знаний — выбирается из настроек агента
          </div>

          <!-- select -->
          <select
            v-else-if="field.field_type === 'select'"
            v-model="localData[field.field_name]"
            class="input text-sm"
            @change="emitUpdate"
          >
            <option value="">— выберите —</option>
            <option v-for="opt in parseOptions(field.options)" :key="opt" :value="opt">{{ opt }}</option>
          </select>

          <!-- json / array -->
          <div v-else-if="field.field_type === 'json' || field.field_type === 'array'">
            <textarea
              v-model="localData[field.field_name]"
              class="input resize-none text-sm font-mono"
              rows="3"
              :placeholder="field.field_type === 'array' ? arrayPlaceholder : jsonPlaceholder"
              @input="emitUpdate"
            />
            <p class="text-xs text-gray-400 mt-0.5">
              {{ field.field_type === 'array' ? 'По одному элементу на строку' : 'Формат JSON' }}
            </p>
          </div>

          <!-- everything else -->
          <input
            v-else
            v-model="localData[field.field_name]"
            class="input text-sm"
            :type="field.field_type === 'number' ? 'number' : 'text'"
            :placeholder="field.hint || ''"
            @input="emitUpdate"
          />
        </template>
      </div>

      <!-- Output fields -->
      <div v-if="outputFields.length" class="pt-3 border-t border-gray-100">
        <div class="text-xs font-medium text-gray-500 mb-2">Передаёт дальше:</div>
        <div class="flex flex-wrap gap-1.5">
          <span
            v-for="out in outputFields"
            :key="out.name"
            class="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded-full border border-green-200"
          >→ {{ out.name }}</span>
        </div>
      </div>
    </div>

    <!-- Delete -->
    <div class="px-4 py-2.5 border-t border-gray-100 shrink-0">
      <button
        class="w-full text-xs text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg py-1.5 transition-colors"
        @click="$emit('delete')"
      >Удалить блок</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useVueFlow } from '@vue-flow/core'
import AiTokenField from '@/components/tools/AiTokenField.vue'

const props = defineProps({
  nodeId: { type: String, required: true },
  nodeType: { type: String, default: 'tool' },
  nodeData: { type: Object, default: () => ({}) },
  agentTool: { type: Object, default: null },
  inputData: { type: Object, default: () => ({}) },
})
const emits = defineEmits(['update', 'close', 'delete'])

const { getEdges, findNode } = useVueFlow()

const SCHEDULE_PRESETS = [
  { label: 'Каждые 15 мин', cron: '*/15 * * * *' },
  { label: 'Каждые 30 мин', cron: '*/30 * * * *' },
  { label: 'Каждый час', cron: '0 * * * *' },
  { label: 'Каждые 2 часа', cron: '0 */2 * * *' },
  { label: 'Каждые 3 часа', cron: '0 */3 * * *' },
  { label: 'Каждые 6 часов', cron: '0 */6 * * *' },
]

const TIMEZONES = [
  { v: 'Europe/Moscow', l: 'Москва (UTC+3)' },
  { v: 'Europe/Kiev', l: 'Киев (UTC+2/3)' },
  { v: 'Asia/Almaty', l: 'Алматы (UTC+5)' },
  { v: 'UTC', l: 'UTC' },
  { v: 'Europe/London', l: 'Лондон' },
]

const triggerLabels = { manual: 'Запуск вручную', cron: 'По расписанию' }

// Tool state — re-init when nodeId or inputData changes
const localData = ref({})

function rebuildLocalData() {
  const base = {}
  for (const f of (props.agentTool?.tool?.fields ?? [])) {
    base[f.field_name] = ''
  }
  localData.value = { ...base, ...(props.inputData || {}) }
}

watch(() => props.nodeId, rebuildLocalData, { immediate: true })
watch(() => props.agentTool, rebuildLocalData, { deep: true })
watch(() => props.inputData, (val) => {
  localData.value = { ...localData.value, ...(val || {}) }
}, { deep: true })

// Trigger state
const triggerLocal = ref({ triggerType: 'manual', schedule: '', timezone: 'Europe/Moscow', label: '', scheduleMode: 'preset' })
watch(() => [props.nodeId, props.nodeData], () => {
  if (props.nodeType === 'trigger') {
    triggerLocal.value = { triggerType: 'manual', schedule: '', timezone: 'Europe/Moscow', label: '', ...props.nodeData }
    // Parse exact time from cron if needed
    const match = (props.nodeData?.schedule || '').match(/^(\d+) (\d+) \* \* \*$/)
    if (match) exactTime.value = `${String(match[2]).padStart(2,'0')}:${String(match[1]).padStart(2,'0')}`
  }
}, { immediate: true, deep: true })

// Output state
const outputLocal = ref({ label: '' })
watch(() => [props.nodeId, props.nodeData], () => {
  if (props.nodeType === 'output') outputLocal.value = { label: '', ...props.nodeData }
}, { immediate: true, deep: true })

// Exact time for cron
const exactTime = ref('')
function applyExactTime() {
  if (!exactTime.value) return
  const [hh, mm] = exactTime.value.split(':')
  triggerLocal.value.schedule = `${parseInt(mm)} ${parseInt(hh)} * * *`
  emitSpecial()
}

const arrayPlaceholder = "Элемент 1\nЭлемент 2\n..."
const jsonPlaceholder = '{"key": "value"}'

const inputFields = computed(() => props.agentTool?.tool?.fields ?? [])
const outputFields = computed(() => props.agentTool?.tool?.output_fields ?? [])

function isConnected(fieldName) {
  return getEdges.value.some((e) => e.target === props.nodeId && e.targetHandle === fieldName)
}

function getConnectionSource(fieldName) {
  const edge = getEdges.value.find((e) => e.target === props.nodeId && e.targetHandle === fieldName)
  if (!edge) return ''
  const srcNode = findNode(edge.source)
  return `🔗 ${srcNode?.data?.toolName ?? edge.source} → ${edge.sourceHandle}`
}

function parseOptions(opts) {
  if (!opts) return []
  if (Array.isArray(opts)) return opts
  try { return JSON.parse(opts) } catch { return String(opts).split('\n').map(s => s.trim()).filter(Boolean) }
}

function emitUpdate() {
  emits('update', { ...localData.value })
}

function emitSpecial() {
  if (props.nodeType === 'trigger') emits('update', { ...triggerLocal.value })
  if (props.nodeType === 'output') emits('update', { ...outputLocal.value })
}
</script>
