<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Загрузка -->
    <div v-if="loading" class="flex justify-center py-16 text-gray-400">Загрузка...</div>

    <template v-else-if="agent">
      <!-- Шапка -->
      <div class="flex items-start justify-between mb-6">
        <div>
          <div class="flex items-center gap-3 mb-1">
            <RouterLink to="/cabinet/office" class="text-gray-400 hover:text-gray-600 text-sm">← Офис</RouterLink>
          </div>
          <div class="flex items-center gap-3">
            <h1 class="text-2xl font-bold text-gray-900">{{ agent.name }}</h1>
            <span :class="agent.is_active ? 'badge-active' : 'badge-inactive'">
              {{ agent.is_active ? 'Активен' : 'Неактивен' }}
            </span>
          </div>
          <p v-if="agent.description" class="text-gray-500 text-sm mt-1">{{ agent.description }}</p>
        </div>
        <button class="btn-secondary text-sm" @click="showEditModal = true">Редактировать</button>
      </div>

      <!-- Двухколоночный layout -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">

        <!-- Левая колонка: Чат -->
        <div class="card flex flex-col" style="min-height: 600px">
          <div class="px-5 py-4 border-b border-gray-100">
            <h2 class="font-semibold text-sm text-gray-700">💬 Чат с агентом</h2>
          </div>
          <ChatWindow
            :agent-id="agent.id"
            :energy-left="agent.energy_left"
            @energy-updated="agent.energy_left = $event"
            @trigger-created="reloadAgent"
            @tool-run="loadRunLogs"
            @settings-saved="reloadAgent"
          />
        </div>

        <!-- Правая колонка: Инструменты + Автозапуски + История -->
        <div class="flex flex-col gap-4">

          <!-- Инструменты -->
          <div class="card p-5">
            <div class="flex items-center justify-between mb-4">
              <h2 class="font-semibold text-sm text-gray-700">🔧 Инструменты</h2>
              <span class="text-xs text-gray-400">{{ agent.agent_tools.length }} / {{ subStore.data?.max_tools_per_agent ?? '—' }}</span>
            </div>
            <div class="grid grid-cols-1 gap-3">
              <ToolCard
                v-for="at in agent.agent_tools"
                :key="at.id"
                :agent-tool="at"
                :agent-id="agent.id"
                @update="handleToolFieldsUpdate"
                @remove="handleRemoveTool"
              />
              <button
                class="border-2 border-dashed border-gray-200 rounded-xl p-4 flex flex-col items-center justify-center gap-2 hover:border-primary-400 hover:bg-primary-50 transition-colors cursor-pointer text-sm text-gray-500"
                @click="handleAddToolClick"
              >
                <span class="text-2xl">+</span>
                <span>Добавить инструмент</span>
              </button>
            </div>
            <p v-if="atToolLimit" class="mt-3 text-xs text-yellow-700 bg-yellow-50 rounded-lg px-3 py-2">
              Достигнут лимит инструментов.
              <a href="https://ascn.ai/pricing" target="_blank" class="underline font-medium">Улучшите подписку →</a>
            </p>
          </div>

          <!-- Автозапуски -->
          <div class="card p-5">
            <h2 class="font-semibold text-sm text-gray-700 mb-4">🕐 Автозапуски</h2>
            <TriggersBlock :agent="agent" />
          </div>

          <!-- История запусков -->
          <div class="card p-5">
            <div class="flex items-center justify-between mb-4">
              <h2 class="font-semibold text-sm text-gray-700">📋 История запусков</h2>
              <button class="text-xs text-primary-600 hover:underline" @click="loadRunLogs">Обновить</button>
            </div>
            <div v-if="runLogs.length === 0" class="text-xs text-gray-400 text-center py-4">
              Пока нет запусков. Нажмите ▶ Запустить на любом инструменте.
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="log in runLogs"
                :key="log.id"
                class="flex items-start gap-3 p-3 rounded-lg border border-gray-100 hover:border-gray-200"
              >
                <div class="shrink-0 mt-0.5 cursor-pointer" @click="openLogDetail(log)">
                  <span v-if="log.status === 'running'" class="inline-block w-4 h-4 border-2 border-primary-400 border-t-transparent rounded-full animate-spin"></span>
                  <span v-else-if="log.status === 'success'" class="text-green-500 text-base leading-none">✅</span>
                  <span v-else-if="log.status === 'cancelled'" class="text-gray-400 text-base leading-none">⏹</span>
                  <span v-else class="text-red-500 text-base leading-none">❌</span>
                </div>
                <div class="flex-1 min-w-0 cursor-pointer" @click="openLogDetail(log)">
                  <div class="flex items-center gap-2">
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
          </div>

        </div>
      </div>
    </template>

    <!-- Модал редактирования -->
    <EditAgentModal
      v-if="showEditModal && agent"
      :agent="agent"
      @close="showEditModal = false"
      @saved="handleAgentSaved"
      @deleted="router.push('/cabinet/office')"
    />

    <!-- Попап: детальный результат запуска -->
    <Teleport to="body">
      <div v-if="selectedLog" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="selectedLog = null">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md flex flex-col" style="max-height: 85vh;">
          <!-- Заголовок -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
            <div class="flex items-center gap-2">
              <span v-if="selectedLog.status === 'success'" class="text-green-500">✅</span>
              <span v-else-if="selectedLog.status === 'error'" class="text-red-500">❌</span>
              <span v-else class="inline-block w-4 h-4 border-2 border-primary-400 border-t-transparent rounded-full animate-spin"></span>
              <h3 class="font-semibold text-gray-900">{{ selectedLog.tool_name }}</h3>
            </div>
            <button class="text-gray-400 hover:text-gray-600" @click="selectedLog = null">✕</button>
          </div>
          <!-- Скроллируемый контент -->
          <div class="px-6 py-4 overflow-y-auto flex-1">
            <div class="flex gap-4 text-xs text-gray-400 mb-4">
              <span>{{ formatDate(selectedLog.started_at) }}</span>
              <span>{{ { manual: '▶ вручную', chat: '💬 чат', auto: '🕐 авто' }[selectedLog.trigger_type] }}</span>
            </div>
            <ResultRenderer :result-json="selectedLog.result_json" :status="selectedLog.status" />
          </div>
          <div class="px-6 pb-4 flex justify-end">
            <button class="btn-secondary text-sm" @click="selectedLog = null">Закрыть</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Попап: лимит инструментов -->
    <UpgradePlanModal
      v-if="showUpgradeModal"
      title="Лимит инструментов достигнут"
      description="На вашем тарифе недоступно добавление новых инструментов агенту. Повысьте тариф для расширения возможностей."
      @close="showUpgradeModal = false"
    />

    <!-- Магазин инструментов (slideout) -->
    <ToolStoreModal
      v-if="showToolStore"
      :excluded-ids="agent?.agent_tools.map(at => at.tool_id) ?? []"
      @close="showToolStore = false"
      @select="handleToolSelect"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

import { useRoute, useRouter } from 'vue-router'
import { useAgentsStore } from '@/stores/agents'
import { useToastStore } from '@/stores/toast'
import { useSubscriptionStore } from '@/stores/subscription'
import { agentsApi } from '@/api/agents'
import ToolCard from '@/components/tools/ToolCard.vue'
import TriggersBlock from '@/components/agents/TriggersBlock.vue'
import ChatWindow from '@/components/chat/ChatWindow.vue'
import EditAgentModal from '@/components/agents/EditAgentModal.vue'
import ToolStoreModal from '@/components/tools/ToolStoreModal.vue'
import UpgradePlanModal from '@/components/UpgradePlanModal.vue'
import ResultRenderer from '@/components/tools/ResultRenderer.vue'

const route = useRoute()
const router = useRouter()
const agentsStore = useAgentsStore()
const toast = useToastStore()
const subStore = useSubscriptionStore()

const loading = ref(true)
const agent = ref(null)
const showEditModal = ref(false)
const showToolStore = ref(false)
const showUpgradeModal = ref(false)
const runLogs = ref([])
const selectedLog = ref(null)

const atToolLimit = computed(() => {
  if (!agent.value || !subStore.data) return false
  return agent.value.agent_tools.length >= subStore.data.max_tools_per_agent
})

onMounted(async () => {
  const agentRes = await agentsStore.fetchAgent(route.params.id).catch(() => null)
  if (agentRes) {
    agent.value = agentRes
    await loadRunLogs()
  }
  loading.value = false
})

async function reloadAgent() {
  const updated = await agentsStore.fetchAgent(route.params.id).catch(() => null)
  if (updated) agent.value = updated
}

async function loadRunLogs() {
  if (!agent.value) return
  try {
    const res = await agentsApi.getRunLogs(agent.value.id)
    runLogs.value = res.data
  } catch { /* тихо */ }
}

function openLogDetail(log) { selectedLog.value = log }

async function deleteLog(logId) {
  if (!confirm('Удалить запись из истории?')) return
  try {
    await agentsApi.deleteRunLog(logId)
    runLogs.value = runLogs.value.filter(l => l.id !== logId)
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

function handleAddToolClick() {
  if (atToolLimit.value) {
    showUpgradeModal.value = true
    return
  }
  showToolStore.value = true
}

async function handleToolSelect(toolId) {
  try {
    const res = await agentsApi.addTool(agent.value.id, toolId)
    agent.value.agent_tools.push(res.data)
    toast.success('Инструмент добавлен')
    showToolStore.value = false
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка добавления инструмента')
  }
}

async function handleRemoveTool(toolId) {
  try {
    await agentsApi.removeTool(agent.value.id, toolId)
    agent.value.agent_tools = agent.value.agent_tools.filter(at => at.tool_id !== toolId)
    toast.success('Инструмент удалён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка удаления инструмента')
  }
}

async function handleToolFieldsUpdate({ toolId, fieldValues }) {
  try {
    const res = await agentsApi.updateToolFields(agent.value.id, toolId, fieldValues)
    const idx = agent.value.agent_tools.findIndex(at => at.tool_id === toolId)
    if (idx !== -1) agent.value.agent_tools[idx] = res.data
    toast.success('Настройки сохранены')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка сохранения')
  }
}

function handleAgentSaved(updated) {
  agent.value = { ...agent.value, ...updated }
  showEditModal.value = false
}
</script>
