<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100">
      <div>
        <div class="font-semibold text-sm text-gray-900">
          <span v-if="nodeType === 'trigger'">{{ triggerLabels[nodeData?.triggerType] ?? 'Триггер' }}</span>
          <span v-else-if="nodeType === 'output'">Точка выхода</span>
          <span v-else>{{ agentTool?.tool?.name }}</span>
        </div>
        <div class="text-xs text-gray-400 mt-0.5">
          <span v-if="nodeType === 'trigger'">Начало цепочки</span>
          <span v-else-if="nodeType === 'output'">Конец цепочки</span>
          <span v-else>⚡ {{ agentTool?.tool?.energy_cost }} за запуск</span>
        </div>
      </div>
      <button class="text-gray-400 hover:text-gray-600 text-lg" @click="$emit('close')">✕</button>
    </div>

    <!-- Trigger config -->
    <div v-if="nodeType === 'trigger'" class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block">Тип триггера</label>
        <select v-model="triggerLocal.triggerType" class="input text-sm" @change="emitSpecial">
          <option value="manual">▶ Вручную</option>
          <option value="chat">💬 Из чата</option>
          <option value="cron">🕐 По расписанию</option>
        </select>
      </div>
      <div v-if="triggerLocal.triggerType === 'cron'">
        <label class="text-xs font-medium text-gray-600 mb-1 block">Расписание (CRON)</label>
        <input v-model="triggerLocal.schedule" class="input text-sm font-mono" placeholder="0 9 * * 1-5" @input="emitSpecial" />
        <p class="text-xs text-gray-400 mt-0.5">Например: <code>0 9 * * 1-5</code> — каждый будний день в 9:00</p>
      </div>
      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block">Метка (необязательно)</label>
        <input v-model="triggerLocal.label" class="input text-sm" placeholder="Мой триггер" @input="emitSpecial" />
      </div>
    </div>

    <!-- Output config -->
    <div v-else-if="nodeType === 'output'" class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block">Webhook URL для отправки результата</label>
        <input v-model="outputLocal.webhook_url" class="input text-sm font-mono" placeholder="https://..." @input="emitSpecial" />
        <p class="text-xs text-gray-400 mt-1">После выполнения цепочки все данные будут отправлены POST-запросом на этот URL</p>
      </div>
      <div>
        <label class="text-xs font-medium text-gray-600 mb-1 block">Метка (необязательно)</label>
        <input v-model="outputLocal.label" class="input text-sm" placeholder="Выход" @input="emitSpecial" />
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
          <span v-if="field.required" class="text-red-500">*</span>
        </label>

        <!-- Connected from another node -->
        <div v-if="isConnected(field.field_name)" class="flex items-center gap-2 px-3 py-2 bg-purple-50 rounded-lg border border-purple-200 text-xs text-purple-700">
          <span>🔗</span>
          <span>Подключено: <strong>{{ getConnectionSource(field.field_name) }}</strong></span>
        </div>

        <!-- Manual input -->
        <template v-else>
          <select v-if="field.field_type === 'select'" v-model="localData[field.field_name]" class="input text-sm" @change="emitUpdate">
            <option value="">— выберите —</option>
            <option v-for="opt in parseOptions(field.options)" :key="opt" :value="opt">{{ opt }}</option>
          </select>
          <textarea
            v-else-if="field.field_type === 'textarea' || field.field_type === 'json' || field.field_type === 'array'"
            v-model="localData[field.field_name]"
            class="input resize-none text-sm font-mono"
            rows="3"
            :placeholder="field.hint || ''"
            @input="emitUpdate"
          />
          <input
            v-else-if="field.field_type !== 'ai_token'"
            v-model="localData[field.field_name]"
            class="input text-sm"
            :placeholder="field.hint || ''"
            @input="emitUpdate"
          />
          <p v-if="field.hint && field.field_type === 'text'" class="text-xs text-gray-400 mt-0.5">{{ field.hint }}</p>
        </template>
      </div>

      <!-- Output fields info -->
      <div v-if="outputFields.length" class="pt-3 border-t border-gray-100">
        <div class="text-xs font-medium text-gray-500 mb-2">Выходные данные:</div>
        <div class="flex flex-wrap gap-1.5">
          <span
            v-for="out in outputFields"
            :key="out.name"
            class="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded-full border border-green-200"
          >
            → {{ out.name }}
          </span>
        </div>
        <p class="text-xs text-gray-400 mt-1">Эти значения можно передать следующим блокам</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useVueFlow } from '@vue-flow/core'

const props = defineProps({
  nodeId: { type: String, required: true },
  nodeType: { type: String, default: 'tool' },
  nodeData: { type: Object, default: () => ({}) },
  agentTool: { type: Object, default: null },
  inputData: { type: Object, default: () => ({}) },
})
const emits = defineEmits(['update', 'close'])

const { getEdges, findNode } = useVueFlow()

// Tool node state
const localData = ref({ ...(props.inputData || {}) })
watch(() => props.inputData, (val) => { localData.value = { ...(val || {}) } }, { deep: true })

// Trigger node state
const triggerLocal = ref({ triggerType: 'manual', schedule: '', timezone: 'UTC', label: '', ...(props.nodeData || {}) })
watch(() => props.nodeData, (val) => {
  if (props.nodeType === 'trigger') triggerLocal.value = { triggerType: 'manual', schedule: '', timezone: 'UTC', label: '', ...(val || {}) }
  if (props.nodeType === 'output') outputLocal.value = { webhook_url: '', label: '', ...(val || {}) }
}, { deep: true })

// Output node state
const outputLocal = ref({ webhook_url: '', label: '', ...(props.nodeData || {}) })

const triggerLabels = { manual: 'Запуск вручную', chat: 'Из чата', cron: 'По расписанию' }

const inputFields = computed(() => props.agentTool?.tool?.fields ?? [])
const outputFields = computed(() => props.agentTool?.tool?.output_fields ?? [])

function isConnected(fieldName) {
  return getEdges.value.some((e) => e.target === props.nodeId && e.targetHandle === fieldName)
}

function getConnectionSource(fieldName) {
  const edge = getEdges.value.find((e) => e.target === props.nodeId && e.targetHandle === fieldName)
  if (!edge) return ''
  const srcNode = findNode(edge.source)
  return `${srcNode?.data?.toolName ?? edge.source} → ${edge.sourceHandle}`
}

function parseOptions(opts) {
  if (!opts) return []
  if (Array.isArray(opts)) return opts
  return String(opts).split('\n').map((s) => s.trim()).filter(Boolean)
}

function emitUpdate() {
  emits('update', { ...localData.value })
}

function emitSpecial() {
  if (props.nodeType === 'trigger') emits('update', { ...triggerLocal.value })
  if (props.nodeType === 'output') emits('update', { ...outputLocal.value })
}
</script>
