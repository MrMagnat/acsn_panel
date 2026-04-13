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
          <div class="flex items-center gap-3 flex-wrap">
            <h1 class="text-2xl font-bold text-gray-900">{{ agent.name }}</h1>
            <span :class="agent.is_active ? 'badge-active' : 'badge-inactive'">
              {{ agent.is_active ? 'Активен' : 'Неактивен' }}
            </span>
            <a
              v-if="agent.is_maintenance"
              href="https://t.me/ascnai_nocode"
              target="_blank"
              rel="noopener"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-orange-100 text-orange-600 text-xs font-medium hover:bg-orange-200 transition-colors"
              title="Агент временно на тех.обслуживании и может работать некорректно — подробнее у менеджера"
            >🔧 тех.обслуживание</a>
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
            :suggestions="agent.prompt_suggestions ?? []"
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

          <!-- Скиллы -->
          <div class="card p-5">
            <div class="flex items-center justify-between mb-4">
              <h2 class="font-semibold text-sm text-gray-700">✨ Скиллы</h2>
            </div>
            <div class="grid grid-cols-1 gap-3">
              <div
                v-for="as_ in agent.agent_skills"
                :key="as_.id"
                class="flex items-center justify-between px-3 py-2.5 rounded-xl border border-gray-100 hover:border-gray-200 group"
              >
                <div class="flex items-center gap-2.5 min-w-0">
                  <span class="text-xl shrink-0">{{ as_.skill.icon }}</span>
                  <div class="min-w-0">
                    <div class="flex items-center gap-1">
                      <div class="text-sm font-medium text-gray-800 truncate">{{ as_.skill.name }}</div>
                      <a
                        v-if="as_.skill.is_maintenance"
                        href="https://t.me/ascnai_nocode"
                        target="_blank"
                        rel="noopener"
                        class="shrink-0 text-orange-500 hover:text-orange-600 text-xs"
                        title="Скилл временно на тех.обслуживании и может работать некорректно — подробнее у менеджера"
                        @click.stop
                      >🔧</a>
                    </div>
                    <div v-if="as_.skill.description" class="text-xs text-gray-400 truncate">{{ as_.skill.description }}</div>
                  </div>
                </div>
                <button
                  class="shrink-0 text-gray-300 hover:text-red-400 transition-colors ml-2 opacity-0 group-hover:opacity-100"
                  @click="removeSkill(as_.skill_id)"
                >✕</button>
              </div>
              <!-- Кнопка добавить — в стиле инструментов -->
              <button
                class="border-2 border-dashed border-gray-200 rounded-xl p-4 flex flex-col items-center justify-center gap-2 hover:border-purple-400 hover:bg-purple-50 transition-colors cursor-pointer text-sm text-gray-500"
                @click="showSkillCatalog = true"
              >
                <span class="text-2xl">✨</span>
                <span>Добавить скилл</span>
              </button>
            </div>
          </div>

          <!-- Воркфлоу -->
          <div class="card p-5">
            <div class="flex items-center justify-between mb-4">
              <h2 class="font-semibold text-sm text-gray-700">⟨⟩ Воркфлоу</h2>
              <button class="text-xs text-primary-600 hover:underline" @click="createWorkflow">+ Новый</button>
            </div>
            <div v-if="workflows.length === 0" class="text-xs text-gray-400 text-center py-3">
              Нет воркфлоу. Создайте цепочку из инструментов.
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="wf in workflows"
                :key="wf.id"
                class="flex items-center justify-between p-2.5 rounded-lg border border-gray-100 hover:border-primary-300 hover:bg-primary-50/40 cursor-pointer transition-colors group"
                @click="router.push(`/cabinet/agents/${agent.id}/workflow/${wf.id}`)"
              >
                <span class="text-sm text-gray-800 font-medium">{{ wf.name }}</span>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-gray-400">{{ wf.graph_json?.nodes?.length ?? 0 }} шагов</span>
                  <button
                    v-if="runningWorkflow === wf.id"
                    class="opacity-100 text-xs px-2 py-0.5 bg-red-100 text-red-600 border border-red-200 rounded-md hover:bg-red-200 transition-all"
                    @click.stop="stopWorkflowFromAgent(wf.id)"
                  >■</button>
                  <button
                    class="opacity-0 group-hover:opacity-100 text-xs px-2 py-0.5 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-all"
                    :class="runningWorkflow === wf.id ? 'opacity-100 !bg-gray-300 cursor-not-allowed' : ''"
                    :disabled="runningWorkflow === wf.id"
                    @click.stop="runWorkflowFromAgent(wf.id)"
                  >{{ runningWorkflow === wf.id ? '⟳' : '▶' }}</button>
                  <button
                    class="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-400 transition-all text-xs"
                    @click.stop="deleteWorkflow(wf.id)"
                  >✕</button>
                </div>
              </div>
            </div>
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

    <!-- Каталог скиллов (slideout) -->
    <Teleport to="body">
      <div v-if="showSkillCatalog" class="fixed inset-0 z-40 flex">
        <div class="flex-1 bg-black/40" @click="showSkillCatalog = false" />
        <div class="w-full max-w-sm bg-white shadow-2xl flex flex-col overflow-hidden">
          <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100 shrink-0">
            <h3 class="font-semibold text-gray-900">✨ Каталог скиллов</h3>
            <button class="text-gray-400 hover:text-gray-600" @click="showSkillCatalog = false">✕</button>
          </div>
          <div class="flex-1 overflow-y-auto p-4 space-y-2">
            <div v-if="skillCatalogLoading" class="text-center py-8 text-gray-400">Загрузка...</div>
            <div v-else-if="!skillCatalog.length" class="text-center py-8 text-gray-400">
              <div class="text-3xl mb-2">✨</div>
              <div>Скиллов пока нет</div>
            </div>
            <div
              v-for="skill in skillCatalog"
              :key="skill.id"
              class="flex items-start gap-3 p-3 rounded-xl border border-gray-100 hover:border-primary-300 hover:bg-primary-50/30 transition-colors"
              :class="isSkillAdded(skill.id) ? 'opacity-50 pointer-events-none' : 'cursor-pointer'"
              @click="addSkill(skill.id)"
            >
              <span class="text-2xl shrink-0">{{ skill.icon }}</span>
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-medium text-sm text-gray-900">{{ skill.name }}</span>
                  <span v-if="isSkillAdded(skill.id)" class="text-xs text-green-600">✓ добавлен</span>
                </div>
                <p v-if="skill.description" class="text-xs text-gray-500 mt-0.5">{{ skill.description }}</p>
                <span v-if="skill.category" class="inline-block mt-1 text-xs px-1.5 py-0.5 bg-purple-50 text-purple-600 rounded-full border border-purple-100">{{ skill.category }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

import { useRoute, useRouter } from 'vue-router'
import { useAgentsStore } from '@/stores/agents'
import { useToastStore } from '@/stores/toast'
import { useSubscriptionStore } from '@/stores/subscription'
import { agentsApi } from '@/api/agents'
import { workflowApi } from '@/api/workflow'
import { skillsApi } from '@/api/skills'
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
const workflows = ref([])
const runningWorkflow = ref(null)
const showSkillCatalog = ref(false)
const skillCatalog = ref([])
const skillCatalogLoading = ref(false)

const atToolLimit = computed(() => {
  if (!agent.value || !subStore.data) return false
  return agent.value.agent_tools.length >= subStore.data.max_tools_per_agent
})

onMounted(async () => {
  const agentRes = await agentsStore.fetchAgent(route.params.id).catch(() => null)
  if (agentRes) {
    agent.value = agentRes
    await Promise.all([loadRunLogs(), loadWorkflows(), loadSkillCatalog()])
  }
  loading.value = false
})

async function loadWorkflows() {
  try {
    const res = await workflowApi.list(route.params.id)
    workflows.value = res.data
  } catch { /* тихо */ }
}

async function createWorkflow() {
  try {
    const res = await workflowApi.create({ agent_id: agent.value.id, name: 'Новый воркфлоу' })
    router.push(`/cabinet/agents/${agent.value.id}/workflow/${res.data.id}`)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка создания воркфлоу')
  }
}

async function stopWorkflowFromAgent(id) {
  try {
    await workflowApi.stop(id)
  } catch { /* тихо */ }
}

async function runWorkflowFromAgent(id) {
  if (runningWorkflow.value) return
  runningWorkflow.value = id
  try {
    const res = await workflowApi.run(id)
    if (res.data.status === 'success') {
      toast.success('Воркфлоу выполнен успешно')
    } else {
      toast.error(res.data.error || 'Ошибка выполнения воркфлоу')
    }
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка запуска воркфлоу')
  } finally {
    runningWorkflow.value = null
  }
}

async function deleteWorkflow(id) {
  if (!confirm('Удалить воркфлоу?')) return
  try {
    await workflowApi.delete(id)
    workflows.value = workflows.value.filter(w => w.id !== id)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка удаления')
  }
}

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

async function loadSkillCatalog() {
  skillCatalogLoading.value = true
  try {
    const res = await skillsApi.list()
    skillCatalog.value = res.data
  } catch { /* тихо */ } finally {
    skillCatalogLoading.value = false
  }
}

function isSkillAdded(skillId) {
  return agent.value?.agent_skills?.some(as => as.skill_id === skillId)
}

async function addSkill(skillId) {
  if (isSkillAdded(skillId)) return
  try {
    const res = await skillsApi.addToAgent(agent.value.id, skillId)
    if (!agent.value.agent_skills) agent.value.agent_skills = []
    agent.value.agent_skills.push(res.data)
    toast.success('Скилл добавлен')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка добавления скилла')
  }
}

async function removeSkill(skillId) {
  try {
    await skillsApi.removeFromAgent(agent.value.id, skillId)
    agent.value.agent_skills = agent.value.agent_skills.filter(as => as.skill_id !== skillId)
    toast.success('Скилл удалён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  }
}
</script>
