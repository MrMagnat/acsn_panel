<template>
  <div class="trigger-node" :class="[`trigger-node--${data.triggerType}`, { 'trigger-node--selected': selected }]">
    <div class="trigger-node__header">
      <span class="trigger-node__icon">{{ icons[data.triggerType] ?? '▶' }}</span>
      <span class="trigger-node__name">{{ labels[data.triggerType] ?? 'Триггер' }}</span>
    </div>
    <div class="trigger-node__body">
      <span v-if="data.triggerType === 'cron' && data.schedule" class="trigger-node__hint">{{ data.schedule }}</span>
      <span v-else class="trigger-node__hint">Начало цепочки</span>
    </div>
    <Handle type="source" id="output" :position="Position.Right" class="trigger-node__handle" />
  </div>
</template>

<script setup>
import { Handle, Position } from '@vue-flow/core'
defineProps({ id: String, data: Object, selected: Boolean })

const icons = { manual: '▶', cron: '🕐' }
const labels = { manual: 'Запуск вручную', cron: 'По расписанию' }
</script>

<style>
.trigger-node {
  background: white;
  border: 2px solid #10b981;
  border-radius: 12px;
  min-width: 180px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: box-shadow 0.15s, border-color 0.15s;
  font-family: inherit;
  position: relative;
}
.trigger-node--selected {
  border-color: #059669;
  box-shadow: 0 0 0 3px rgba(16,185,129,0.2), 0 4px 12px rgba(0,0,0,0.12);
}
.trigger-node--cron { border-color: #8b5cf6; }
.trigger-node--cron.trigger-node--selected { box-shadow: 0 0 0 3px rgba(139,92,246,0.2); }
.trigger-node__header {
  background: #10b981;
  border-radius: 10px 10px 0 0;
  padding: 8px 12px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
.trigger-node--cron .trigger-node__header { background: #8b5cf6; }
.trigger-node__name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.trigger-node__body {
  padding: 8px 12px;
}
.trigger-node__hint { font-size: 11px; color: #6b7280; }
.trigger-node__handle {
  width: 10px !important;
  height: 10px !important;
  border-radius: 50% !important;
  background: #10b981 !important;
  border: 2px solid #10b981 !important;
  right: -6px !important;
}
</style>
