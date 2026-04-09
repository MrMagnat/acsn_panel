<template>
  <div class="p-8 max-w-5xl">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Тарифы</h1>
      <p class="text-sm text-gray-400 mt-1">Управление тарифными планами платформы и синхронизация с ASCN</p>
    </div>

    <!-- Вкладки -->
    <div class="flex gap-1 p-1 bg-gray-100 rounded-xl mb-6 w-fit">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="px-4 py-1.5 text-sm rounded-lg transition-colors font-medium"
        :class="activeTab === tab.id ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
        @click="activeTab = tab.id"
      >{{ tab.label }}</button>
    </div>

    <!-- ── Вкладка 1: Мои тарифы ── -->
    <div v-if="activeTab === 'plans'">
      <div class="flex items-center justify-between mb-4">
        <p class="text-sm text-gray-500">Создайте тарифные планы платформы с лимитами и количеством токенов</p>
        <button class="btn-primary text-sm" @click="openCreateModal">+ Создать тариф</button>
      </div>

      <div v-if="plansLoading" class="text-center py-16 text-gray-400">Загрузка...</div>

      <div v-else-if="!plans.length" class="text-center py-16 text-gray-400">
        <div class="text-4xl mb-3">📋</div>
        <div>Тарифных планов пока нет</div>
        <div class="text-sm mt-1">Создайте первый тариф</div>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="plan in plans"
          :key="plan.id"
          class="card p-4 flex items-center gap-4"
        >
          <!-- Порядок + статус -->
          <div class="shrink-0 w-8 text-center text-sm text-gray-400 font-mono">{{ plan.sort_order }}</div>

          <!-- Основная инфа -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-0.5">
              <span class="font-semibold text-gray-900">{{ plan.name }}</span>
              <span class="text-xs font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{{ plan.slug }}</span>
              <span v-if="plan.is_default" class="text-xs px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">по умолчанию</span>
              <span v-if="!plan.is_active" class="text-xs px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-500">неактивен</span>
            </div>
            <div v-if="plan.description" class="text-xs text-gray-500 truncate mb-1">{{ plan.description }}</div>
            <div class="flex items-center gap-3 text-xs text-gray-500">
              <span>👤 {{ plan.max_agents }} аг.</span>
              <span>🔧 {{ plan.max_tools_per_agent }} инстр./аг.</span>
              <span>⟨⟩ {{ plan.max_workflows }} вф.</span>
              <span>🪙 {{ plan.tokens_per_month.toLocaleString('ru') }} ток./мес</span>
              <span v-if="plan.price_rub === 0" class="text-green-600">Бесплатно</span>
              <span v-else class="text-gray-700 font-medium">{{ (plan.price_rub / 100).toFixed(0) }} ₽/мес</span>
            </div>
          </div>

          <!-- Действия -->
          <div class="flex items-center gap-2 shrink-0">
            <button class="text-xs text-primary-600 hover:underline" @click="openEditModal(plan)">Редактировать</button>
            <button class="text-xs text-red-400 hover:text-red-600" @click="deletePlan(plan)">Удалить</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Вкладка 2: Синхронизация ASCN ── -->
    <div v-if="activeTab === 'ascn'">
      <div class="flex items-center justify-between mb-4">
        <p class="text-sm text-gray-500">Привяжи ASCN-тариф к локальному плану. При входе пользователя применяется соответствующий план.</p>
        <button class="btn-primary text-sm" :disabled="mappingsSaving" @click="saveMappings">
          {{ mappingsSaving ? 'Сохраняю...' : 'Сохранить' }}
        </button>
      </div>

      <div v-if="mappingsLoading" class="text-center py-16 text-gray-400">Загрузка...</div>

      <div v-else class="space-y-3">
        <div
          v-for="(row, idx) in mappings"
          :key="idx"
          class="card p-4 grid grid-cols-12 gap-3 items-center"
        >
          <!-- ASCN Slug -->
          <div class="col-span-3">
            <label class="text-xs text-gray-400 mb-1 block">Slug ASCN</label>
            <input v-model="row.slug" class="input text-xs font-mono" placeholder="no-code-pro" />
          </div>
          <!-- Название (информационное) -->
          <div class="col-span-2">
            <label class="text-xs text-gray-400 mb-1 block">Название</label>
            <input v-model="row.name" class="input text-xs" placeholder="No-Code Pro" />
          </div>
          <!-- Локальный тариф -->
          <div class="col-span-4">
            <label class="text-xs text-gray-400 mb-1 block">→ Локальный тариф</label>
            <select v-model="row.local_plan_slug" class="input text-xs">
              <option value="">— не привязан —</option>
              <option v-for="p in plans" :key="p.slug" :value="p.slug">{{ p.name }} ({{ p.slug }})</option>
            </select>
          </div>
          <!-- Удалить -->
          <div class="col-span-3 flex justify-end pt-4">
            <button class="text-xs text-red-400 hover:text-red-600" @click="mappings.splice(idx, 1)">✕ Удалить</button>
          </div>
        </div>

        <button
          class="w-full py-3 border-2 border-dashed border-gray-200 text-gray-400 hover:border-primary-300 hover:text-primary-500 rounded-xl text-sm transition-colors"
          @click="mappings.push({ slug: '', name: '', local_plan_slug: '' })"
        >
          + Добавить маппинг
        </button>
      </div>

      <!-- Слаги из БД -->
      <div v-if="ascnSlugs.length" class="mt-4 p-4 bg-gray-50 rounded-xl">
        <div class="text-xs font-medium text-gray-500 mb-2">Слаги ASCN у ваших пользователей:</div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="s in ascnSlugs"
            :key="s.slug"
            class="px-2 py-1 bg-white border border-gray-200 rounded-lg text-xs font-mono text-gray-700 hover:border-purple-400 hover:text-purple-700 transition-colors"
            :title="`${s.count} пользователей — нажми чтобы добавить`"
            @click="addMappingWithSlug(s.slug)"
          >
            {{ s.slug }} <span class="text-gray-400">({{ s.count }})</span>
          </button>
        </div>
      </div>

      <div class="mt-4 p-4 bg-blue-50 rounded-xl text-xs text-blue-600 space-y-1">
        <div class="font-medium">Как работает синхронизация:</div>
        <div>• При каждом входе — запрашиваем подписку из ASCN API и берём slug тарифа</div>
        <div>• Slug ищем в таблице выше → находим → применяем связанный локальный тариф</div>
        <div>• Токены (energy) ASCN берутся из <code class="bg-blue-100 px-1 rounded">nocode_credits_count</code> 1:1</div>
        <div>• Тариф <strong>default</strong> — применяется если у пользователя нет активной подписки ASCN</div>
      </div>
    </div>
  </div>

  <!-- Модал создания/редактирования тарифа -->
  <Teleport to="body">
    <div v-if="showPlanModal" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="showPlanModal = false">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 class="font-semibold text-gray-900">{{ editingPlan?.id ? 'Редактировать тариф' : 'Создать тариф' }}</h3>
          <button class="text-gray-400 hover:text-gray-600" @click="showPlanModal = false">✕</button>
        </div>
        <div class="px-6 py-4 space-y-3 max-h-[70vh] overflow-y-auto">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Название *</label>
              <input v-model="planForm.name" class="input text-sm" placeholder="Базовый" />
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Slug *</label>
              <input v-model="planForm.slug" class="input text-sm font-mono" placeholder="base" />
            </div>
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600 mb-1 block">Описание</label>
            <textarea v-model="planForm.description" class="input text-sm resize-none" rows="2" placeholder="Для малого бизнеса..." />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Цена (руб/мес)</label>
              <input v-model.number="planForm.price_rub" type="number" min="0" class="input text-sm" placeholder="0" />
              <p class="text-xs text-gray-400 mt-0.5">0 = бесплатно</p>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Токенов в месяц</label>
              <input v-model.number="planForm.tokens_per_month" type="number" min="0" class="input text-sm" />
            </div>
          </div>
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Агентов</label>
              <input v-model.number="planForm.max_agents" type="number" min="1" class="input text-sm" />
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Инстр./агент</label>
              <input v-model.number="planForm.max_tools_per_agent" type="number" min="1" class="input text-sm" />
            </div>
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Воркфлоу</label>
              <input v-model.number="planForm.max_workflows" type="number" min="0" class="input text-sm" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium text-gray-600 mb-1 block">Порядок сортировки</label>
              <input v-model.number="planForm.sort_order" type="number" class="input text-sm" />
            </div>
          </div>
          <div class="flex items-center gap-4 pt-1">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="planForm.is_active" class="rounded" />
              <span class="text-sm text-gray-700">Активен</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="planForm.is_default" class="rounded" />
              <span class="text-sm text-gray-700">По умолчанию</span>
              <span class="text-xs text-gray-400">(для новых пользователей)</span>
            </label>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-2">
          <button class="btn-secondary text-sm" @click="showPlanModal = false">Отмена</button>
          <button class="btn-primary text-sm" :disabled="planSaving" @click="savePlan">
            {{ planSaving ? 'Сохраняю...' : (editingPlan?.id ? 'Сохранить' : 'Создать') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

const tabs = [
  { id: 'plans', label: 'Мои тарифы' },
  { id: 'ascn', label: 'Синхронизация ASCN' },
]
const activeTab = ref('plans')

// ── Тарифные планы ──
const plans = ref([])
const plansLoading = ref(true)
const showPlanModal = ref(false)
const planSaving = ref(false)
const editingPlan = ref(null)

const PLAN_DEFAULTS = {
  name: '',
  slug: '',
  description: '',
  price_rub: 0,
  max_agents: 3,
  max_tools_per_agent: 3,
  max_workflows: 3,
  tokens_per_month: 1000,
  is_active: true,
  is_default: false,
  sort_order: 0,
}
const planForm = ref({ ...PLAN_DEFAULTS })

async function loadPlans() {
  plansLoading.value = true
  try {
    const res = await adminApi.getTariffPlans()
    plans.value = res.data
  } catch {
    toast.error('Ошибка загрузки тарифов')
  } finally {
    plansLoading.value = false
  }
}

function openCreateModal() {
  editingPlan.value = {}
  planForm.value = { ...PLAN_DEFAULTS }
  showPlanModal.value = true
}

function openEditModal(plan) {
  editingPlan.value = plan
  planForm.value = {
    name: plan.name,
    slug: plan.slug,
    description: plan.description || '',
    price_rub: plan.price_rub,
    max_agents: plan.max_agents,
    max_tools_per_agent: plan.max_tools_per_agent,
    max_workflows: plan.max_workflows,
    tokens_per_month: plan.tokens_per_month,
    is_active: plan.is_active,
    is_default: plan.is_default,
    sort_order: plan.sort_order,
  }
  showPlanModal.value = true
}

async function savePlan() {
  if (!planForm.value.name || !planForm.value.slug) {
    toast.error('Заполните название и slug')
    return
  }
  planSaving.value = true
  try {
    if (editingPlan.value?.id) {
      const res = await adminApi.updateTariffPlan(editingPlan.value.id, planForm.value)
      const idx = plans.value.findIndex(p => p.id === editingPlan.value.id)
      if (idx !== -1) plans.value[idx] = res.data
    } else {
      const res = await adminApi.createTariffPlan(planForm.value)
      plans.value.push(res.data)
    }
    showPlanModal.value = false
    toast.success('Тариф сохранён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка сохранения')
  } finally {
    planSaving.value = false
  }
}

async function deletePlan(plan) {
  if (!confirm(`Удалить тариф «${plan.name}»?`)) return
  try {
    await adminApi.deleteTariffPlan(plan.id)
    plans.value = plans.value.filter(p => p.id !== plan.id)
    toast.success('Тариф удалён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка удаления')
  }
}

// ── ASCN маппинг ──
const mappings = ref([])
const ascnSlugs = ref([])
const mappingsLoading = ref(true)
const mappingsSaving = ref(false)

async function loadMappings() {
  mappingsLoading.value = true
  try {
    const [mappingsRes, slugsRes] = await Promise.all([
      adminApi.getTariffMappings(),
      adminApi.getAscnSlugs(),
    ])
    mappings.value = mappingsRes.data.map(m => ({ ...m, local_plan_slug: m.local_plan_slug || '' }))
    ascnSlugs.value = slugsRes.data
  } catch {
    toast.error('Ошибка загрузки маппинга')
  } finally {
    mappingsLoading.value = false
  }
}

function addMappingWithSlug(slug) {
  if (mappings.value.some(m => m.slug === slug)) return
  mappings.value.push({ slug, name: slug, local_plan_slug: '' })
}

async function saveMappings() {
  mappingsSaving.value = true
  try {
    await adminApi.saveTariffMappings(mappings.value)
    toast.success('Маппинг сохранён')
  } catch {
    toast.error('Ошибка сохранения')
  } finally {
    mappingsSaving.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadPlans(), loadMappings()])
})
</script>
