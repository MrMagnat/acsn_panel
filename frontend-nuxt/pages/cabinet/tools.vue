<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold text-gray-900 mb-2">Готовые инструменты</h1>
    <p class="text-gray-500 text-sm mb-6">Воркфлоу-инструменты доступные для добавления вашим агентам</p>

    <div v-if="toolsStore.loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="tool in toolsStore.tools"
        :key="tool.id"
        class="card p-5 flex flex-col gap-2"
      >
        <div class="flex items-start justify-between">
          <h3 class="font-semibold text-gray-900">{{ tool.name }}</h3>
          <span class="badge-active text-xs">Активен</span>
        </div>
        <p class="text-sm text-gray-500 flex-1">{{ tool.description || 'Без описания' }}</p>
        <div class="flex items-center justify-between mt-2 pt-2 border-t border-gray-50">
          <span class="text-xs text-gray-400">⚡ {{ tool.energy_cost }} за вызов</span>
          <span class="text-xs text-gray-400">{{ tool.fields?.length ?? 0 }} полей</span>
        </div>
      </div>
    </div>

    <div v-if="!toolsStore.loading && toolsStore.tools.length === 0" class="text-center py-16 text-gray-400">
      Инструменты ещё не добавлены администратором
    </div>
  </div>
</template>

<script setup>
import { useToolsStore } from '~/stores/tools'

definePageMeta({ layout: 'cabinet', middleware: 'auth' })

const toolsStore = useToolsStore()

onMounted(() => toolsStore.fetchTools())
</script>
