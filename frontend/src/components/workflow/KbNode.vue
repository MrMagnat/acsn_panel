<template>
  <div class="kb-node" :class="[`kb-node--${data.operation}`, { 'kb-node--selected': selected }]">
    <div class="kb-node__header">
      <span>{{ data.operation === 'read' ? '📥' : '📤' }}</span>
      <span class="kb-node__name">{{ data.operation === 'read' ? 'Получить из базы' : 'Записать в базу' }}</span>
    </div>
    <div class="kb-node__body">
      <span class="kb-node__hint">{{ data.kb_name || '— база не выбрана —' }}</span>
    </div>
    <Handle type="target" id="__entry__" :position="Position.Left" class="kb-node__handle kb-node__handle--in" />
    <Handle type="source" id="records" :position="Position.Right" class="kb-node__handle kb-node__handle--out" />
  </div>
</template>

<script setup>
import { Handle, Position } from '@vue-flow/core'
defineProps({ id: String, data: Object, selected: Boolean })
</script>

<style>
.kb-node {
  background: white;
  border: 2px solid #3b82f6;
  border-radius: 12px;
  min-width: 180px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: box-shadow 0.15s, border-color 0.15s;
  font-family: inherit;
  position: relative;
}
.kb-node--selected { border-color: #1d4ed8; box-shadow: 0 0 0 3px rgba(59,130,246,0.2), 0 4px 12px rgba(0,0,0,0.12); }
.kb-node--write { border-color: #f59e0b; }
.kb-node--write.kb-node--selected { box-shadow: 0 0 0 3px rgba(245,158,11,0.2); }
.kb-node__header {
  background: #3b82f6;
  border-radius: 10px 10px 0 0;
  padding: 8px 12px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
.kb-node--write .kb-node__header { background: #f59e0b; }
.kb-node__name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kb-node__body { padding: 8px 12px; }
.kb-node__hint { font-size: 11px; color: #6b7280; }
.kb-node__handle--in {
  width: 10px !important; height: 10px !important;
  border-radius: 3px !important;
  background: #6b7280 !important;
  border: 2px solid #6b7280 !important;
  left: -6px !important;
}
.kb-node__handle--out {
  width: 10px !important; height: 10px !important;
  border-radius: 50% !important;
  background: #3b82f6 !important;
  border: 2px solid #3b82f6 !important;
  right: -6px !important;
}
.kb-node--write .kb-node__handle--out { background: #f59e0b !important; border-color: #f59e0b !important; }
</style>
