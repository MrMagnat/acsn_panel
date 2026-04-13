<template>
  <!-- Оверлей -->
  <div class="fixed inset-0 bg-black/40 z-40 flex items-center justify-center p-4" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">

      <!-- Заголовок -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <h2 class="font-semibold text-gray-900">{{ stepTitle }}</h2>
        <button class="text-gray-400 hover:text-gray-600 text-xl" @click="$emit('close')">✕</button>
      </div>

      <!-- Шаг 1: выбор типа -->
      <div v-if="step === 'choose'" class="p-6 grid grid-cols-2 gap-4">
        <button
          class="card p-6 flex flex-col items-center gap-3 hover:shadow-md hover:border-primary-300 transition-all cursor-pointer border-2 border-transparent"
          @click="step = 'template'"
        >
          <div class="text-4xl">🤖</div>
          <div class="font-semibold text-gray-900">Шаблонный агент</div>
          <div class="text-xs text-gray-400 text-center">Готовый агент с преднастроенными инструментами</div>
        </button>
        <button
          class="card p-6 flex flex-col items-center gap-3 hover:shadow-md hover:border-primary-300 transition-all cursor-pointer border-2 border-transparent"
          @click="step = 'custom'"
        >
          <div class="text-4xl">✨</div>
          <div class="font-semibold text-gray-900">Создать своего</div>
          <div class="text-xs text-gray-400 text-center">Настройте агента под свои задачи</div>
        </button>
      </div>

      <!-- Шаг 2а: шаблонные агенты -->
      <div v-else-if="step === 'template'" class="flex flex-col flex-1 overflow-hidden">
        <div class="p-4 overflow-y-auto flex-1">
          <div v-if="loadingTemplates" class="text-center py-8 text-gray-400">Загрузка...</div>
          <div v-else class="grid grid-cols-2 gap-3">
            <button
              v-for="t in templates"
              :key="t.id"
              class="card p-4 text-left hover:shadow-md hover:border-primary-300 transition-all cursor-pointer border-2 border-transparent"
              :disabled="creating"
              @click="t.is_maintenance ? (maintenanceTemplate = t) : selectTemplate(t)"
            >
              <div class="flex items-center gap-1.5">
                <div class="font-semibold text-sm text-gray-900">{{ t.name }}</div>
                <button
                  v-if="t.is_maintenance"
                  class="text-orange-500 hover:text-orange-600 text-xs"
                  @click.stop="maintenanceTemplate = t"
                >🔧</button>
              </div>
              <div class="text-xs text-gray-500 mt-1 line-clamp-2">{{ t.description || 'Без описания' }}</div>
              <div class="mt-2 flex flex-wrap gap-1">
                <span v-if="t.is_maintenance" class="text-xs px-1.5 py-0.5 rounded-full bg-orange-100 text-orange-600 font-medium">тех.обслуживание</span>
                <span v-for="tool in t.tools" :key="tool.id" class="badge-inactive text-xs">{{ tool.name }}</span>
              </div>
            </button>
          </div>
          <div v-if="!loadingTemplates && templates.length === 0" class="text-center py-8 text-gray-400">
            Нет доступных шаблонов
          </div>
        </div>
        <div class="px-4 pb-4">
          <button class="btn-secondary text-sm" @click="step = 'choose'">← Назад</button>
        </div>
      </div>

      <!-- Шаг 2б: создание своего -->
      <div v-else-if="step === 'custom'" class="flex flex-col flex-1 overflow-hidden">
        <form class="p-6 overflow-y-auto flex-1 space-y-4" @submit.prevent="createCustom">
          <div>
            <label class="label">Название агента *</label>
            <input v-model="customForm.name" class="input" placeholder="Мой ассистент" required />
          </div>
          <div>
            <label class="label">Описание</label>
            <textarea v-model="customForm.description" class="input resize-none h-20" placeholder="Чем занимается этот агент..."></textarea>
          </div>

          <!-- Выбор инструментов -->
          <div>
            <label class="label">Инструменты ({{ selectedToolIds.length }} / {{ maxTools }})</label>
            <div v-if="loadingTools" class="text-sm text-gray-400">Загрузка...</div>
            <div v-else class="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1">
              <label
                v-for="tool in allTools"
                :key="tool.id"
                class="flex items-start gap-2 p-3 rounded-lg border cursor-pointer transition-colors text-sm"
                :class="selectedToolIds.includes(tool.id)
                  ? 'border-primary-400 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'"
              >
                <input
                  type="checkbox"
                  :value="tool.id"
                  v-model="selectedToolIds"
                  :disabled="!selectedToolIds.includes(tool.id) && selectedToolIds.length >= maxTools"
                  class="mt-0.5 shrink-0"
                />
                <div>
                  <div class="font-medium text-gray-800">{{ tool.name }}</div>
                  <div class="text-xs text-gray-400 line-clamp-1">{{ tool.description }}</div>
                </div>
              </label>
            </div>
            <p v-if="selectedToolIds.length >= maxTools" class="text-xs text-yellow-600 mt-1">
              Достигнут лимит инструментов для вашей подписки
            </p>
          </div>

          <div class="flex gap-3 pt-2">
            <button type="button" class="btn-secondary" @click="step = 'choose'">← Назад</button>
            <button type="submit" class="btn-primary" :disabled="creating || !customForm.name">
              {{ creating ? 'Создаю...' : 'Создать агента' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <MaintenanceModal
    :show="!!maintenanceTemplate"
    :label="maintenanceTemplate?.name || 'Агент'"
    @close="maintenanceTemplate = null"
    @continue="doSelectTemplate(maintenanceTemplate); maintenanceTemplate = null"
  />

  <!-- Попап лимита подписки -->
  <UpgradePlanModal
    v-if="showUpgradeModal"
    title="Лимит агентов достигнут"
    description="На вашем тарифе недоступно добавление новых агентов. Повысьте тариф, чтобы создавать больше ИИ-агентов."
    @close="showUpgradeModal = false"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAgentsStore } from '@/stores/agents'
import { useToolsStore } from '@/stores/tools'
import { useToastStore } from '@/stores/toast'
import { toolsApi } from '@/api/tools'
import { useSubscriptionStore } from '@/stores/subscription'
import UpgradePlanModal from '@/components/UpgradePlanModal.vue'
import MaintenanceModal from '@/components/MaintenanceModal.vue'

const emit = defineEmits(['close', 'created'])

const agentsStore = useAgentsStore()
const toolsStore = useToolsStore()
const toast = useToastStore()
const subStore = useSubscriptionStore()

const step = ref('choose')
const templates = ref([])
const maintenanceTemplate = ref(null)
const loadingTemplates = ref(false)
const loadingTools = ref(false)
const creating = ref(false)
const maxTools = ref(2)
const selectedToolIds = ref([])
const customForm = ref({ name: '', description: '' })
const showUpgradeModal = ref(false)

const stepTitle = computed(() => ({
  choose: 'Добавить агента',
  template: 'Выбрать шаблон',
  custom: 'Новый агент',
}[step.value]))

const allTools = computed(() => toolsStore.tools)

onMounted(async () => {
  // Загружаем шаблоны и инструменты параллельно
  loadingTemplates.value = true
  loadingTools.value = true

  await Promise.allSettled([
    toolsStore.fetchTools(),
    toolsApi.listTemplateAgents().then((r) => { templates.value = r.data }),
  ])

  maxTools.value = subStore.data?.max_tools_per_agent ?? 2

  loadingTemplates.value = false
  loadingTools.value = false
})

async function doSelectTemplate(template) {
  await selectTemplate(template)
}

async function selectTemplate(template) {
  creating.value = true
  try {
    const agent = await agentsStore.createFromTemplate(template.id)
    toast.success(`Агент "${agent.name}" добавлен`)
    emit('created', agent)
  } catch (e) {
    if (e.response?.status === 403) {
      showUpgradeModal.value = true
    } else {
      toast.error(e.response?.data?.detail || 'Ошибка добавления агента')
    }
  } finally {
    creating.value = false
  }
}

async function createCustom() {
  creating.value = true
  try {
    const agent = await agentsStore.createAgent({
      name: customForm.value.name,
      description: customForm.value.description,
      tool_ids: selectedToolIds.value,
    })
    toast.success(`Агент "${agent.name}" создан`)
    emit('created', agent)
  } catch (e) {
    if (e.response?.status === 403) {
      showUpgradeModal.value = true
    } else {
      toast.error(e.response?.data?.detail || 'Ошибка создания агента')
    }
  } finally {
    creating.value = false
  }
}
</script>
