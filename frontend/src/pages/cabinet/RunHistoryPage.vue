<template>
  <div class="p-8 max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">История запусков</h1>
        <p class="text-gray-500 text-sm mt-1">Все запуски инструментов по всем агентам и разовые запуски</p>
      </div>
      <button class="btn-secondary text-sm" @click="load">Обновить</button>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <div v-else-if="logs.length === 0" class="text-center py-16 text-gray-400">
      Пока нет запусков
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="log in logs"
        :key="log.id"
        class="flex items-start gap-3 p-4 rounded-xl border border-gray-100 bg-white hover:border-gray-200 cursor-pointer"
        @click="openDetail(log)"
      >
        <div class="shrink-0 mt-0.5">
          <span v-if="log.status === 'running'" class="inline-block w-4 h-4 border-2 border-primary-400 border-t-transparent rounded-full animate-spin"></span>
          <span v-else-if="log.status === 'success'" class="text-green-500 text-base leading-none">✅</span>
          <span v-else-if="log.status === 'cancelled'" class="text-gray-400 text-base leading-none">⏹</span>
          <span v-else class="text-red-500 text-base leading-none">❌</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-medium text-sm text-gray-800">{{ log.tool_name }}</span>
            <span class="text-xs px-1.5 py-0.5 rounded-full"
              :class="{
                'bg-gray-100 text-gray-500': log.trigger_type === 'manual',
                'bg-blue-100 text-blue-600': log.trigger_type === 'chat',
                'bg-purple-100 text-purple-600': log.trigger_type === 'auto',
              }">
              {{ { manual: '▶ вручную', chat: '💬 чат', auto: '🕐 авто' }[log.trigger_type] ?? log.trigger_type }}
            </span>
          </div>
          <div class="text-xs text-gray-400 mt-0.5">{{ formatDate(log.started_at) }}</div>
          <div v-if="log.status !== 'running' && log.result_json" class="text-xs text-gray-500 mt-1 truncate">
            {{ summarizeResult(log.result_json) }}
          </div>
        </div>
        <button
          class="shrink-0 text-gray-300 hover:text-red-400 transition-colors mt-0.5"
          title="Удалить"
          @click.stop="deleteLog(log.id)"
        >🗑</button>
      </div>
    </div>

    <!-- Попап детального результата -->
    <Teleport to="body">
      <div v-if="selectedLog" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="selectedLog = null">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md flex flex-col" style="max-height: 85vh;">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
            <div class="flex items-center gap-2">
              <span v-if="selectedLog.status === 'success'" class="text-green-500">✅</span>
              <span v-else-if="selectedLog.status === 'error'" class="text-red-500">❌</span>
              <span v-else-if="selectedLog.status === 'cancelled'" class="text-gray-400">⏹</span>
              <span v-else class="inline-block w-4 h-4 border-2 border-primary-400 border-t-transparent rounded-full animate-spin"></span>
              <h3 class="font-semibold text-gray-900">{{ selectedLog.tool_name }}</h3>
            </div>
            <button class="text-gray-400 hover:text-gray-600" @click="selectedLog = null">✕</button>
          </div>
          <div class="px-6 py-4 overflow-y-auto flex-1">
            <div class="flex gap-4 text-xs text-gray-400 mb-4">
              <span>{{ formatDate(selectedLog.started_at) }}</span>
              <span>{{ { manual: '▶ вручную', chat: '💬 чат', auto: '🕐 авто' }[selectedLog.trigger_type] ?? selectedLog.trigger_type }}</span>
            </div>
            <ResultRenderer :result-json="selectedLog.result_json" :status="selectedLog.status" />
          </div>
          <div class="px-6 pb-4 flex justify-end">
            <button class="btn-secondary text-sm" @click="selectedLog = null">Закрыть</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { toolsApi } from '@/api/tools'
import { agentsApi } from '@/api/agents'
import ResultRenderer from '@/components/tools/ResultRenderer.vue'

const loading = ref(true)
const logs = ref([])
const selectedLog = ref(null)

onMounted(load)

async function load() {
  loading.value = true
  try {
    const res = await toolsApi.getAllRunLogs()
    logs.value = res.data
  } finally {
    loading.value = false
  }
}

function openDetail(log) {
  selectedLog.value = log
}

async function deleteLog(logId) {
  if (!confirm('Удалить запись из истории?')) return
  try {
    await agentsApi.deleteRunLog(logId)
    logs.value = logs.value.filter(l => l.id !== logId)
    if (selectedLog.value?.id === logId) selectedLog.value = null
  } catch {
    alert('Не удалось удалить запись')
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function summarizeResult(jsonStr) {
  try {
    const d = JSON.parse(jsonStr)
    if (d.error) return '❌ ' + d.error
    const vals = Object.entries(d).slice(0, 3).map(([k, v]) => `${k}: ${v}`).join(' · ')
    return vals || JSON.stringify(d).slice(0, 80)
  } catch { return jsonStr?.slice(0, 80) }
}
</script>
