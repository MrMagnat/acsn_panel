<template>
  <div class="output-node" :class="{ 'output-node--selected': selected }">
    <Handle type="target" id="input" :position="Position.Left" class="output-node__handle" />
    <div class="output-node__header">
      <span>🏁</span>
      <span class="output-node__name">{{ data.label || 'Точка выхода' }}</span>
    </div>
    <div class="output-node__body">
      <span v-if="data.webhook_url" class="output-node__url">{{ data.webhook_url }}</span>
      <span v-else class="output-node__hint">Нажми для настройки URL</span>
    </div>
  </div>
</template>

<script setup>
import { Handle, Position } from '@vue-flow/core'
defineProps({ id: String, data: Object, selected: Boolean })
</script>

<style>
.output-node {
  background: white;
  border: 2px solid #6366f1;
  border-radius: 12px;
  min-width: 180px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: box-shadow 0.15s, border-color 0.15s;
  font-family: inherit;
  position: relative;
}
.output-node--selected {
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.2), 0 4px 12px rgba(0,0,0,0.12);
}
.output-node__header {
  background: #6366f1;
  border-radius: 10px 10px 0 0;
  padding: 8px 12px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
.output-node__name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.output-node__body { padding: 8px 12px; }
.output-node__url {
  font-size: 11px;
  color: #4f46e5;
  display: block;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.output-node__hint { font-size: 11px; color: #9ca3af; }
.output-node__handle {
  width: 10px !important;
  height: 10px !important;
  border-radius: 50% !important;
  background: white !important;
  border: 2px solid #6366f1 !important;
  left: -6px !important;
}
</style>
