<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Пользователи</h1>

    <!-- Фильтры -->
    <div class="flex gap-3 mb-4">
      <select v-model="filterPlan" class="input max-w-[160px]" @change="load">
        <option value="">Все тарифы</option>
        <option value="free">Free</option>
        <option value="pro">Pro</option>
        <option value="business">Business</option>
      </select>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <div v-else class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="text-left px-4 py-3 text-gray-500 font-medium">Пользователь</th>
            <th class="text-left px-4 py-3 text-gray-500 font-medium">Тариф</th>
            <th class="text-left px-4 py-3 text-gray-500 font-medium">Агентов</th>
            <th class="text-left px-4 py-3 text-gray-500 font-medium">Инструментов</th>
            <th class="text-left px-4 py-3 text-gray-500 font-medium">Дата</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50/50">
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <img
                  v-if="user.avatar_url"
                  :src="user.avatar_url"
                  class="w-8 h-8 rounded-full object-cover shrink-0"
                  :alt="user.name"
                />
                <div v-else class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0 text-primary-600 font-semibold text-xs">
                  {{ user.name.charAt(0).toUpperCase() }}
                </div>
                <div>
                  <div class="font-medium text-gray-900">{{ user.name }}</div>
                  <div class="text-gray-400 text-xs">{{ user.email }}</div>
                  <div v-if="user.telegram || user.phone" class="text-gray-400 text-xs mt-0.5 flex gap-2">
                    <span v-if="user.telegram">@{{ user.telegram }}</span>
                    <span v-if="user.phone">{{ user.phone }}</span>
                  </div>
                </div>
              </div>
            </td>
            <td class="px-4 py-3">
              <div v-if="user.tariff_plan_name" class="text-xs font-medium text-gray-800">{{ user.tariff_plan_name }}</div>
              <div class="text-xs text-gray-400">{{ user.plan }}</div>
              <span v-if="user.is_admin" class="badge-warning mt-0.5 inline-block">Admin</span>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ user.agents_count }}</td>
            <td class="px-4 py-3 text-gray-600">{{ user.tools_count }}</td>
            <td class="px-4 py-3 text-gray-400 text-xs">{{ formatDate(user.created_at) }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <button class="text-xs text-primary-600 hover:underline" @click="openProfile(user)">Управление</button>
                <button class="text-xs text-red-500 hover:text-red-700 hover:underline" @click="confirmDelete(user)">Удалить</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Профиль пользователя — правая панель -->
    <Teleport to="body">
      <div v-if="profileUser" class="fixed inset-0 z-40 flex">
        <!-- Затемнение -->
        <div class="flex-1 bg-black/40" @click="closeProfile" />
        <!-- Панель -->
        <div class="w-full max-w-lg bg-white shadow-2xl flex flex-col overflow-hidden">
          <!-- Шапка -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-bold">
                {{ profileUser.name.charAt(0).toUpperCase() }}
              </div>
              <div>
                <div class="font-semibold text-gray-900">{{ profileUser.name }}</div>
                <div class="text-xs text-gray-400">{{ profileUser.email }}</div>
              </div>
            </div>
            <button class="text-gray-400 hover:text-gray-600 text-xl leading-none" @click="closeProfile">✕</button>
          </div>

          <!-- Контент -->
          <div class="flex-1 overflow-y-auto divide-y divide-gray-100">

            <!-- 1. Профиль -->
            <div class="px-6 py-5">
              <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Профиль</div>
              <form @submit.prevent="saveProfile" class="space-y-3">
                <div>
                  <label class="label">Имя</label>
                  <input v-model="profileForm.name" class="input" />
                </div>
                <div class="flex items-center gap-2">
                  <input type="checkbox" v-model="profileForm.is_admin" class="w-4 h-4" id="chk-admin" />
                  <label for="chk-admin" class="text-sm text-gray-700 cursor-pointer">Администратор</label>
                </div>
                <button type="submit" class="btn-primary text-sm" :disabled="profileSaving">
                  {{ profileSaving ? '...' : 'Сохранить профиль' }}
                </button>
              </form>
            </div>

            <!-- 2. Тариф -->
            <div class="px-6 py-5">
              <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Тарифный план</div>
              <div class="space-y-3">
                <div>
                  <label class="label">Назначить тариф</label>
                  <select v-model="tariffForm.tariff_plan_id" class="input text-sm">
                    <option value="">— без тарифа —</option>
                    <option v-for="p in availablePlans" :key="p.id" :value="p.id">{{ p.name }} ({{ p.slug }})</option>
                  </select>
                </div>
                <div>
                  <label class="label">Дополнительно добавить токены</label>
                  <input v-model.number="tariffForm.add_tokens" type="number" min="0" class="input text-sm" placeholder="0" />
                </div>
                <button class="btn-primary text-sm" :disabled="tariffSaving" @click="applyTariff">
                  {{ tariffSaving ? '...' : 'Применить тариф' }}
                </button>
              </div>
            </div>

            <!-- 3. Agents Token -->
            <div class="px-6 py-5">
              <div class="flex items-center justify-between mb-3">
                <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Agents Token</div>
                <div v-if="profileData" class="text-sm font-bold text-gray-900">
                  {{ profileData.tokens_left.toLocaleString('ru') }}
                  <span class="text-xs font-normal text-gray-400">токенов</span>
                </div>
              </div>
              <div class="space-y-2">
                <div class="flex gap-2">
                  <button
                    class="flex-1 py-1.5 text-xs rounded-lg border transition-colors"
                    :class="tokenMode === 'add' ? 'border-green-400 bg-green-50 text-green-700 font-medium' : 'border-gray-200 text-gray-500'"
                    @click="tokenMode = 'add'"
                  >+ Начислить</button>
                  <button
                    class="flex-1 py-1.5 text-xs rounded-lg border transition-colors"
                    :class="tokenMode === 'sub' ? 'border-red-400 bg-red-50 text-red-700 font-medium' : 'border-gray-200 text-gray-500'"
                    @click="tokenMode = 'sub'"
                  >− Списать</button>
                </div>
                <div class="flex gap-2">
                  <input
                    v-model.number="tokenAmount"
                    type="number"
                    min="1"
                    class="input flex-1 text-sm"
                    placeholder="Количество"
                  />
                  <input
                    v-model="tokenDesc"
                    class="input flex-1 text-sm"
                    placeholder="Причина"
                  />
                  <button class="btn-primary text-sm shrink-0" :disabled="!tokenAmount || tokenSaving" @click="applyTokens">
                    {{ tokenSaving ? '...' : 'ОК' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- 4. AI Баланс -->
            <div class="px-6 py-5">
              <div class="flex items-center justify-between mb-3">
                <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider">AI Баланс</div>
                <div v-if="profileData" class="text-sm font-bold" :class="profileData.balance_usd > 0 ? 'text-green-600' : 'text-gray-400'">
                  ${{ (profileData.balance_usd / 10000).toFixed(4).replace(/\.?0+$/, '') }}
                </div>
              </div>
              <div class="space-y-2">
                <div class="flex gap-2">
                  <button
                    class="flex-1 py-1.5 text-xs rounded-lg border transition-colors"
                    :class="balanceMode === 'add' ? 'border-green-400 bg-green-50 text-green-700 font-medium' : 'border-gray-200 text-gray-500'"
                    @click="balanceMode = 'add'"
                  >+ Начислить</button>
                  <button
                    class="flex-1 py-1.5 text-xs rounded-lg border transition-colors"
                    :class="balanceMode === 'sub' ? 'border-red-400 bg-red-50 text-red-700 font-medium' : 'border-gray-200 text-gray-500'"
                    @click="balanceMode = 'sub'"
                  >− Списать</button>
                </div>
                <div class="flex gap-2 items-center">
                  <input
                    v-model.number="balanceAmount"
                    type="number"
                    min="1"
                    class="input flex-1 text-sm"
                    placeholder="Единицы (1 = $0.0001)"
                  />
                  <button class="btn-primary text-sm shrink-0" :disabled="!balanceAmount || balanceSaving" @click="applyBalance">
                    {{ balanceSaving ? '...' : 'ОК' }}
                  </button>
                </div>
                <p class="text-xs text-gray-400">Вводите в единицах: 10000 = $1.00</p>
              </div>
            </div>

            <!-- 5. История транзакций -->
            <div class="px-6 py-5">
              <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">История токенов</div>
              <div v-if="profileLoading" class="text-sm text-gray-400 text-center py-4">Загрузка...</div>
              <div v-else-if="!profileData?.transactions?.length" class="text-sm text-gray-400 text-center py-4">
                Транзакций пока нет
              </div>
              <div v-else class="space-y-1">
                <div
                  v-for="tx in profileData.transactions"
                  :key="tx.id"
                  class="flex items-start justify-between py-2 border-b border-gray-50 last:border-0"
                >
                  <div class="min-w-0">
                    <div class="text-sm text-gray-800">{{ tx.description }}</div>
                    <div class="text-xs text-gray-400 mt-0.5">
                      {{ formatDateTime(tx.created_at) }}
                      <span v-if="tx.tool_name" class="ml-1">· {{ tx.tool_name }}</span>
                    </div>
                  </div>
                  <span
                    class="text-sm font-semibold ml-4 shrink-0"
                    :class="tx.amount > 0 ? 'text-green-600' : 'text-red-500'"
                  >
                    {{ tx.amount > 0 ? '+' : '' }}{{ tx.amount }}
                  </span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const users = ref([])
const loading = ref(true)
const filterPlan = ref('')

// Профиль
const profileUser = ref(null)
const profileData = ref(null)
const profileLoading = ref(false)
const profileForm = ref({ name: '', is_admin: false })
const profileSaving = ref(false)

// Тариф
const tariffForm = ref({ tariff_plan_id: '', add_tokens: 0 })
const tariffSaving = ref(false)
const availablePlans = ref([])

// Agents Token
const tokenMode = ref('add')
const tokenAmount = ref(null)
const tokenDesc = ref('')
const tokenSaving = ref(false)

// AI Баланс
const balanceMode = ref('add')
const balanceAmount = ref(null)
const balanceSaving = ref(false)

onMounted(async () => {
  await load()
  try {
    const res = await adminApi.getTariffPlans()
    availablePlans.value = res.data
  } catch {}
})

async function load() {
  loading.value = true
  try {
    const res = await adminApi.getUsers(filterPlan.value ? { plan: filterPlan.value } : {})
    users.value = res.data
  } finally {
    loading.value = false
  }
}

async function openProfile(user) {
  profileUser.value = user
  profileForm.value = { name: user.name, is_admin: user.is_admin }
  tariffForm.value = { tariff_plan_id: '', add_tokens: 0 }
  tokenMode.value = 'add'
  tokenAmount.value = null
  tokenDesc.value = ''
  balanceMode.value = 'add'
  balanceAmount.value = null
  profileData.value = null
  profileLoading.value = true
  try {
    const res = await adminApi.getUserEnergy(user.id)
    profileData.value = res.data
  } catch {
    toast.error('Не удалось загрузить данные пользователя')
  } finally {
    profileLoading.value = false
  }
}

function closeProfile() {
  profileUser.value = null
  profileData.value = null
}

async function saveProfile() {
  profileSaving.value = true
  try {
    const res = await adminApi.updateUser(profileUser.value.id, profileForm.value)
    const idx = users.value.findIndex((u) => u.id === profileUser.value.id)
    if (idx !== -1) users.value[idx] = res.data
    profileUser.value = { ...profileUser.value, ...profileForm.value }
    toast.success('Профиль сохранён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  } finally {
    profileSaving.value = false
  }
}

async function applyTariff() {
  tariffSaving.value = true
  try {
    await adminApi.setUserTariff(profileUser.value.id, tariffForm.value)
    toast.success('Тариф применён')
    tariffForm.value = { tariff_plan_id: '', add_tokens: 0 }
    // Обновить tokens_left если были добавлены токены
    if (profileData.value && tariffForm.value.add_tokens) {
      profileData.value.tokens_left += tariffForm.value.add_tokens
    }
    await refreshData()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  } finally {
    tariffSaving.value = false
  }
}

async function applyTokens() {
  if (!tokenAmount.value) return
  tokenSaving.value = true
  try {
    const amount = tokenMode.value === 'add' ? Math.abs(tokenAmount.value) : -Math.abs(tokenAmount.value)
    await adminApi.adjustUserTokens(profileUser.value.id, {
      amount,
      description: tokenDesc.value,
    })
    toast.success(`Токены обновлены: ${amount > 0 ? '+' : ''}${amount}`)
    tokenAmount.value = null
    tokenDesc.value = ''
    await refreshData()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  } finally {
    tokenSaving.value = false
  }
}

async function applyBalance() {
  if (!balanceAmount.value) return
  balanceSaving.value = true
  try {
    const amount = balanceMode.value === 'add' ? Math.abs(balanceAmount.value) : -Math.abs(balanceAmount.value)
    const res = await adminApi.adjustUserBalance(profileUser.value.id, {
      amount,
      description: balanceMode.value === 'add' ? 'Пополнение администратором' : 'Списание администратором',
    })
    if (profileData.value) profileData.value.balance_usd = res.data.balance_usd
    toast.success('Баланс обновлён')
    balanceAmount.value = null
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  } finally {
    balanceSaving.value = false
  }
}

async function refreshData() {
  try {
    const res = await adminApi.getUserEnergy(profileUser.value.id)
    profileData.value = res.data
  } catch {}
}

function confirmDelete(user) {
  if (confirm(`Удалить пользователя ${user.email}?\n\nВсе данные (агенты, инструменты, история) будут удалены безвозвратно.`)) {
    deleteUser(user)
  }
}

async function deleteUser(user) {
  try {
    await adminApi.deleteUser(user.id)
    users.value = users.value.filter((u) => u.id !== user.id)
    if (profileUser.value?.id === user.id) closeProfile()
    toast.success(`Пользователь ${user.email} удалён`)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка при удалении')
  }
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('ru-RU')
}

function formatDateTime(d) {
  return new Date(d).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>
