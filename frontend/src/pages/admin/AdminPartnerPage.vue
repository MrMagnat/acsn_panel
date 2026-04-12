<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Партнёрская программа</h1>

    <!-- Табы -->
    <div class="flex gap-1 mb-6 bg-gray-100 rounded-xl p-1 w-fit">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="activeTab === tab.id ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
        @click="activeTab = tab.id"
      >{{ tab.label }}</button>
    </div>

    <!-- Таб: Настройки -->
    <div v-if="activeTab === 'settings'">
      <div class="card p-6 max-w-md">
        <h2 class="font-semibold text-gray-800 mb-4">Настройки программы</h2>
        <div class="mb-4">
          <label class="text-xs font-medium text-gray-600 mb-1 block">Токенов на $1</label>
          <input v-model.number="tokenRate" type="number" min="1" class="input w-full" placeholder="1000" />
          <p class="text-xs text-gray-400 mt-1">Сколько партнёрских токенов = 1 доллар при выводе</p>
        </div>
        <button class="btn-primary text-sm" :disabled="savingSettings" @click="saveSettings">
          {{ savingSettings ? 'Сохраняю...' : 'Сохранить' }}
        </button>
      </div>
    </div>

    <!-- Таб: Партнёры -->
    <div v-if="activeTab === 'partners'">
      <div v-if="loadingPartners" class="text-center py-16 text-gray-400">Загрузка...</div>
      <div v-else-if="partners.length === 0" class="card p-8 text-center text-gray-400 text-sm">
        Нет пользователей с партнёрским балансом
      </div>
      <div v-else>
        <div class="card overflow-hidden mb-6">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 border-b border-gray-100">
              <tr>
                <th class="text-left px-4 py-3 text-gray-500 font-medium">Пользователь</th>
                <th class="text-right px-4 py-3 text-gray-500 font-medium">Баланс токенов</th>
                <th class="px-4 py-3 text-gray-500 font-medium text-right">Действия</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr
                v-for="p in partners"
                :key="p.user_id"
                class="hover:bg-gray-50/50 cursor-pointer"
                :class="selectedPartner?.user_id === p.user_id ? 'bg-primary-50' : ''"
                @click="selectPartner(p)"
              >
                <td class="px-4 py-3">
                  <div class="font-medium text-gray-900">{{ p.name || '—' }}</div>
                  <div class="text-xs text-gray-400">{{ p.email }}</div>
                </td>
                <td class="px-4 py-3 text-right font-semibold text-gray-900">
                  {{ p.partner_tokens.toLocaleString('ru') }}
                </td>
                <td class="px-4 py-3 text-right">
                  <button class="btn-primary text-xs mr-2" @click.stop="openAdjust(p, 1)">Начислить</button>
                  <button class="btn-secondary text-xs" @click.stop="openAdjust(p, -1)">Списать</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- История транзакций выбранного партнёра -->
        <div v-if="selectedPartner">
          <h2 class="font-semibold text-gray-800 mb-3">
            История транзакций: {{ selectedPartner.name || selectedPartner.email }}
          </h2>
          <div v-if="loadingTxs" class="text-center py-8 text-gray-400 text-sm">Загрузка...</div>
          <div v-else-if="partnerTxs.length === 0" class="card p-6 text-center text-gray-400 text-sm">Транзакций нет</div>
          <div v-else class="card overflow-hidden">
            <table class="w-full text-sm">
              <thead class="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th class="text-left px-4 py-3 text-gray-500 font-medium">Инструмент</th>
                  <th class="text-left px-4 py-3 text-gray-500 font-medium">Описание</th>
                  <th class="text-right px-4 py-3 text-gray-500 font-medium">Токены</th>
                  <th class="text-right px-4 py-3 text-gray-500 font-medium">Дата</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="tx in partnerTxs" :key="tx.id">
                  <td class="px-4 py-3 text-gray-700">{{ tx.tool_name || '—' }}</td>
                  <td class="px-4 py-3 text-gray-500">{{ tx.description }}</td>
                  <td class="px-4 py-3 text-right font-medium" :class="tx.amount > 0 ? 'text-green-600' : 'text-red-500'">
                    {{ tx.amount > 0 ? '+' : '' }}{{ tx.amount }}
                  </td>
                  <td class="px-4 py-3 text-right text-gray-400 text-xs">{{ formatDate(tx.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Таб: Заявки на вывод -->
    <div v-if="activeTab === 'withdrawals'">
      <div v-if="loadingWithdrawals" class="text-center py-16 text-gray-400">Загрузка...</div>
      <div v-else-if="withdrawals.length === 0" class="card p-8 text-center text-gray-400 text-sm">
        Заявок на вывод нет
      </div>
      <div v-else class="card overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-100">
            <tr>
              <th class="text-left px-4 py-3 text-gray-500 font-medium">Пользователь</th>
              <th class="text-right px-4 py-3 text-gray-500 font-medium">Сумма токенов</th>
              <th class="text-left px-4 py-3 text-gray-500 font-medium">Комментарий</th>
              <th class="text-left px-4 py-3 text-gray-500 font-medium">Статус</th>
              <th class="text-right px-4 py-3 text-gray-500 font-medium">Дата</th>
              <th class="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="req in withdrawals" :key="req.id" class="hover:bg-gray-50/50">
              <td class="px-4 py-3">
                <div class="font-medium text-gray-900">{{ req.name || '—' }}</div>
                <div class="text-xs text-gray-400">{{ req.email }}</div>
              </td>
              <td class="px-4 py-3 text-right font-semibold text-gray-900">{{ req.amount.toLocaleString('ru') }}</td>
              <td class="px-4 py-3 text-gray-500 max-w-xs truncate">{{ req.comment || '—' }}</td>
              <td class="px-4 py-3">
                <span
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                  :class="{
                    'bg-yellow-100 text-yellow-700': req.status === 'pending',
                    'bg-green-100 text-green-700': req.status === 'done',
                    'bg-red-100 text-red-700': req.status === 'rejected',
                  }"
                >{{ statusLabel(req.status) }}</span>
                <div v-if="req.admin_note" class="text-xs text-gray-400 mt-1">{{ req.admin_note }}</div>
              </td>
              <td class="px-4 py-3 text-right text-gray-400 text-xs">{{ formatDate(req.created_at) }}</td>
              <td class="px-4 py-3">
                <div v-if="req.status === 'pending'" class="flex gap-2 justify-end">
                  <button class="btn-primary text-xs" @click="handleWithdrawal(req, 'done')">Выполнить</button>
                  <button class="btn-secondary text-xs" @click="openReject(req)">Отклонить</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Модал корректировки токенов -->
    <Teleport to="body">
      <div v-if="adjustModal.show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="adjustModal.show = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm mx-4 p-6">
          <h3 class="font-semibold text-gray-900 mb-4">
            {{ adjustModal.sign > 0 ? 'Начислить токены' : 'Списать токены' }}
          </h3>
          <div class="mb-3">
            <label class="text-xs font-medium text-gray-600 mb-1 block">Количество</label>
            <input v-model.number="adjustModal.amount" type="number" min="1" class="input w-full" />
          </div>
          <div class="mb-5">
            <label class="text-xs font-medium text-gray-600 mb-1 block">Причина</label>
            <input v-model="adjustModal.description" type="text" class="input w-full" placeholder="Описание" />
          </div>
          <div class="flex gap-2 justify-end">
            <button class="btn-secondary text-sm" @click="adjustModal.show = false">Отмена</button>
            <button class="btn-primary text-sm" :disabled="adjustModal.saving || !adjustModal.amount" @click="submitAdjust">
              {{ adjustModal.saving ? 'Сохраняю...' : 'Применить' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Модал отклонения заявки -->
    <Teleport to="body">
      <div v-if="rejectModal.show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="rejectModal.show = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm mx-4 p-6">
          <h3 class="font-semibold text-gray-900 mb-4">Отклонить заявку</h3>
          <div class="mb-5">
            <label class="text-xs font-medium text-gray-600 mb-1 block">Причина отклонения</label>
            <textarea v-model="rejectModal.note" class="input w-full" rows="3" placeholder="Введите причину..."></textarea>
          </div>
          <div class="flex gap-2 justify-end">
            <button class="btn-secondary text-sm" @click="rejectModal.show = false">Отмена</button>
            <button class="btn-primary text-sm" :disabled="rejectModal.saving" @click="submitReject">
              {{ rejectModal.saving ? 'Сохраняю...' : 'Отклонить' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { adminApi } from '@/api/admin'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

const tabs = [
  { id: 'settings', label: 'Настройки' },
  { id: 'partners', label: 'Партнёры' },
  { id: 'withdrawals', label: 'Заявки на вывод' },
]
const activeTab = ref('settings')

// Настройки
const tokenRate = ref(1000)
const savingSettings = ref(false)

// Партнёры
const partners = ref([])
const loadingPartners = ref(false)
const selectedPartner = ref(null)
const partnerTxs = ref([])
const loadingTxs = ref(false)

// Заявки
const withdrawals = ref([])
const loadingWithdrawals = ref(false)

// Модалы
const adjustModal = ref({ show: false, partner: null, sign: 1, amount: null, description: '', saving: false })
const rejectModal = ref({ show: false, req: null, note: '', saving: false })

onMounted(async () => {
  await loadSettings()
})

watch(activeTab, async (tab) => {
  if (tab === 'partners' && partners.value.length === 0) await loadPartners()
  if (tab === 'withdrawals' && withdrawals.value.length === 0) await loadWithdrawals()
})

async function loadSettings() {
  try {
    const res = await adminApi.getPartnerSettings()
    tokenRate.value = res.data.partner_token_rate
  } catch (e) {
    toast.error('Ошибка загрузки настроек')
  }
}

async function saveSettings() {
  savingSettings.value = true
  try {
    await adminApi.savePartnerSettings({ partner_token_rate: tokenRate.value })
    toast.success('Настройки сохранены')
  } catch (e) {
    toast.error('Ошибка сохранения')
  } finally {
    savingSettings.value = false
  }
}

async function loadPartners() {
  loadingPartners.value = true
  try {
    const res = await adminApi.getPartners()
    partners.value = res.data
  } catch (e) {
    toast.error('Ошибка загрузки партнёров')
  } finally {
    loadingPartners.value = false
  }
}

async function selectPartner(p) {
  selectedPartner.value = p
  loadingTxs.value = true
  try {
    const res = await adminApi.getPartnerTransactions(p.user_id)
    partnerTxs.value = res.data
  } catch (e) {
    toast.error('Ошибка загрузки транзакций')
  } finally {
    loadingTxs.value = false
  }
}

function openAdjust(partner, sign) {
  adjustModal.value = { show: true, partner, sign, amount: null, description: '', saving: false }
}

async function submitAdjust() {
  const m = adjustModal.value
  if (!m.amount) return
  m.saving = true
  try {
    const amount = m.sign * Math.abs(m.amount)
    await adminApi.adjustPartnerTokens(m.partner.user_id, { amount, description: m.description })
    toast.success('Баланс обновлён')
    m.show = false
    await loadPartners()
    if (selectedPartner.value?.user_id === m.partner.user_id) {
      await selectPartner(m.partner)
    }
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  } finally {
    m.saving = false
  }
}

async function loadWithdrawals() {
  loadingWithdrawals.value = true
  try {
    const res = await adminApi.getWithdrawRequests()
    withdrawals.value = res.data
  } catch (e) {
    toast.error('Ошибка загрузки заявок')
  } finally {
    loadingWithdrawals.value = false
  }
}

async function handleWithdrawal(req, status) {
  try {
    await adminApi.updateWithdrawRequest(req.id, { status })
    toast.success(status === 'done' ? 'Заявка выполнена' : 'Заявка отклонена')
    await loadWithdrawals()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  }
}

function openReject(req) {
  rejectModal.value = { show: true, req, note: '', saving: false }
}

async function submitReject() {
  const m = rejectModal.value
  m.saving = true
  try {
    await adminApi.updateWithdrawRequest(m.req.id, { status: 'rejected', admin_note: m.note })
    toast.success('Заявка отклонена')
    m.show = false
    await loadWithdrawals()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  } finally {
    m.saving = false
  }
}

function statusLabel(s) {
  return { pending: 'Ожидает', done: 'Выполнена', rejected: 'Отклонена' }[s] || s
}

function formatDate(d) {
  return new Date(d).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>
