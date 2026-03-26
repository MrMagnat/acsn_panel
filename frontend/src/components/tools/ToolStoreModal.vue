<template>
  <div class="fixed inset-0 bg-black/40 z-40 flex items-end sm:items-center justify-center p-4" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-xl max-h-[80vh] flex flex-col">
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <h2 class="font-semibold text-gray-900">Магазин инструментов</h2>
        <button class="text-gray-400 hover:text-gray-600 text-xl" @click="$emit('close')">✕</button>
      </div>

      <div class="flex-1 overflow-y-auto p-4">
        <div v-if="toolsStore.loading" class="text-center py-8 text-gray-400">Загрузка...</div>
        <div v-else class="grid grid-cols-1 gap-3">
          <div
            v-for="tool in availableTools"
            :key="tool.id"
            class="card p-4 flex items-center justify-between hover:shadow-md transition-shadow"
          >
            <div class="flex-1 min-w-0">
              <div class="font-medium text-sm text-gray-900">{{ tool.name }}</div>
              <div class="text-xs text-gray-400 mt-0.5 line-clamp-1">{{ tool.description }}</div>
              <div class="text-xs text-gray-400 mt-1">⚡ {{ tool.energy_cost }} энергии за вызов</div>
            </div>
            <button class="btn-primary text-xs ml-4 shrink-0" @click="$emit('select', tool.id)">
              Добавить
            </button>
          </div>
        </div>
        <div v-if="!toolsStore.loading && availableTools.length === 0" class="text-center py-8 text-gray-400">
          Все доступные инструменты уже добавлены
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useToolsStore } from '@/stores/tools'

const props = defineProps({
  excludedIds: { type: Array, default: () => [] },
})
defineEmits(['close', 'select'])

const toolsStore = useToolsStore()

const availableTools = computed(() =>
  toolsStore.tools.filter((t) => !props.excludedIds.includes(t.id))
)

onMounted(() => {
  if (toolsStore.tools.length === 0) toolsStore.fetchTools()
})
</script>
