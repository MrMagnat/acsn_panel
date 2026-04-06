<template>
  <div
    class="tool-node"
    :class="{ 'tool-node--selected': selected }"
  >
    <!-- Header -->
    <div class="tool-node__header" :style="{ background: accentColor }">
      <span class="tool-node__name">{{ data.toolName || 'Инструмент' }}</span>
    </div>

    <!-- Input handles (left) -->
    <div class="tool-node__inputs">
      <div
        v-for="field in inputFields"
        :key="'in-' + field.field_name"
        class="tool-node__port tool-node__port--in"
      >
        <Handle
          type="target"
          :id="field.field_name"
          :position="Position.Left"
          class="tool-node__handle tool-node__handle--in"
          :class="{ 'tool-node__handle--connected': isInputConnected(field.field_name) }"
        />
        <span class="tool-node__port-label tool-node__port-label--in" :class="{ 'connected': isInputConnected(field.field_name) }">
          {{ isInputConnected(field.field_name) ? '🔗 ' : '' }}{{ field.field_name }}
        </span>
      </div>
    </div>

    <!-- Output handles (right) -->
    <div class="tool-node__outputs">
      <div
        v-for="outField in outputFields"
        :key="'out-' + outField.name"
        class="tool-node__port tool-node__port--out"
      >
        <span class="tool-node__port-label tool-node__port-label--out">{{ outField.name }}</span>
        <Handle
          type="source"
          :id="outField.name"
          :position="Position.Right"
          class="tool-node__handle tool-node__handle--out"
        />
      </div>
    </div>

    <!-- Footer: config summary -->
    <div class="tool-node__footer">
      <span v-if="configuredCount > 0" class="tool-node__status tool-node__status--ok">
        ✓ {{ configuredCount }} заполнено
      </span>
      <span v-if="missingRequired > 0" class="tool-node__status tool-node__status--warn">
        ! {{ missingRequired }} обязательных пусто
      </span>
      <span v-if="configuredCount === 0 && missingRequired === 0" class="tool-node__status tool-node__status--empty">
        Нажми для настройки
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Handle, Position, useVueFlow } from '@vue-flow/core'

const props = defineProps({
  id: String,
  data: Object,
  selected: Boolean,
})

const { getEdges } = useVueFlow()

const COLORS = ['#7c3aed', '#2563eb', '#059669', '#dc2626', '#d97706', '#0891b2']
const accentColor = computed(() => {
  const idx = Math.abs(props.id?.charCodeAt(0) ?? 0) % COLORS.length
  return COLORS[idx]
})

const inputFields = computed(() => props.data?.fields ?? [])
const outputFields = computed(() => props.data?.outputFields ?? [])

function isInputConnected(fieldName) {
  return getEdges.value.some(
    (e) => e.target === props.id && e.targetHandle === fieldName
  )
}

const configuredCount = computed(() => {
  const data = props.data?.input_data ?? {}
  return Object.values(data).filter((v) => v !== '' && v !== null && v !== undefined).length
})

const missingRequired = computed(() => {
  const data = props.data?.input_data ?? {}
  return inputFields.value.filter(
    (f) => f.required && !isInputConnected(f.field_name) && !data[f.field_name]
  ).length
})
</script>

<style>
.tool-node {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  min-width: 200px;
  max-width: 240px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: box-shadow 0.15s, border-color 0.15s;
  font-family: inherit;
}
.tool-node--selected {
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124,58,237,0.15), 0 4px 12px rgba(0,0,0,0.12);
}
.tool-node__header {
  border-radius: 10px 10px 0 0;
  padding: 8px 12px;
  color: white;
  font-size: 13px;
  font-weight: 600;
}
.tool-node__name {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tool-node__inputs,
.tool-node__outputs {
  padding: 6px 0;
}
.tool-node__port {
  display: flex;
  align-items: center;
  height: 26px;
  position: relative;
}
.tool-node__port--in {
  padding-left: 8px;
  justify-content: flex-start;
}
.tool-node__port--out {
  padding-right: 8px;
  justify-content: flex-end;
}
.tool-node__handle {
  width: 10px !important;
  height: 10px !important;
  border-radius: 50% !important;
  border: 2px solid !important;
}
.tool-node__handle--in {
  left: -6px !important;
  background: white !important;
  border-color: #6b7280 !important;
}
.tool-node__handle--in.tool-node__handle--connected {
  background: #7c3aed !important;
  border-color: #7c3aed !important;
}
.tool-node__handle--out {
  right: -6px !important;
  background: #10b981 !important;
  border-color: #10b981 !important;
}
.tool-node__port-label {
  font-size: 11px;
  color: #6b7280;
  user-select: none;
}
.tool-node__port-label--in { padding-left: 10px; }
.tool-node__port-label--in.connected { color: #7c3aed; font-weight: 500; }
.tool-node__port-label--out { padding-right: 10px; color: #059669; }
.tool-node__footer {
  border-top: 1px solid #f3f4f6;
  padding: 5px 10px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tool-node__status {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
}
.tool-node__status--ok { background: #d1fae5; color: #065f46; }
.tool-node__status--warn { background: #fef3c7; color: #92400e; }
.tool-node__status--empty { color: #9ca3af; }
</style>
