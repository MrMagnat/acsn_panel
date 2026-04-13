<template>
  <div
    class="card p-5 flex flex-col gap-3 cursor-pointer hover:shadow-md transition-shadow min-h-[160px]"
    @click="agent.is_maintenance ? showMaintenance = true : $emit('click')"
  >
    <!-- Шапка: название и статус -->
    <div class="flex items-start justify-between gap-2">
      <div class="flex items-center gap-1.5 min-w-0">
        <h3 class="font-semibold text-gray-900 text-sm leading-tight line-clamp-2">{{ agent.name }}</h3>
        <button
          v-if="agent.is_maintenance"
          class="shrink-0 text-orange-500 hover:text-orange-600 text-base leading-none"
          @click.stop="showMaintenance = true"
        >🔧</button>
      </div>
      <span :class="agent.is_active ? 'badge-active' : 'badge-inactive'" class="shrink-0">
        {{ agent.is_active ? 'Активен' : 'Неактивен' }}
      </span>
    </div>

    <!-- Инструменты -->
    <div class="flex items-center gap-1.5 text-xs text-gray-500 mt-auto">
      <span>🔧</span>
      <span>{{ agent.tools_count }} {{ toolsLabel(agent.tools_count) }}</span>
    </div>
  </div>

  <MaintenanceModal
    :show="showMaintenance"
    :label="agent.name"
    @close="showMaintenance = false"
    @continue="showMaintenance = false; $emit('click')"
  />
</template>

<script setup>
import { ref } from 'vue'
import MaintenanceModal from '@/components/MaintenanceModal.vue'

const props = defineProps({
  agent: { type: Object, required: true },
})
defineEmits(['click'])

const showMaintenance = ref(false)

function toolsLabel(n) {
  if (n === 1) return 'инструмент'
  if (n >= 2 && n <= 4) return 'инструмента'
  return 'инструментов'
}
</script>
