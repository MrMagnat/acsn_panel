<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Пользователи</h1>

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
              <div class="font-medium text-gray-900">{{ user.name }}</div>
              <div class="text-gray-400 text-xs">{{ user.email }}</div>
            </td>
            <td class="px-4 py-3">
              <span class="badge-inactive capitalize">{{ user.plan }}</span>
              <span v-if="user.is_admin" class="badge-warning ml-1">Admin</span>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ user.agents_count }}</td>
            <td class="px-4 py-3 text-gray-600">{{ user.tools_count }}</td>
            <td class="px-4 py-3 text-gray-400 text-xs">{{ formatDate(user.created_at) }}</td>
            <td class="px-4 py-3">
              <div class="flex gap-2">
                <button class="text-xs text-primary-600 hover:underline" @click="openEdit(user)">Изменить</button>
                <button class="text-xs text-yellow-600 hover:underline" @click="openEnergy(user)">⚡ Токены</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="editUser" class="fixed inset-0 bg-black/40 z-40 flex items-center justify-center p-4" @click.self="editUser = null">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
        <h2 class="font-semibold mb-4">Редактировать пользователя</h2>
        <form @submit.prevent="saveUser" class="space-y-3">
          <div>
            <label class="label">Имя</label>
            <input v-model="editForm.name" class="input" />
          </div>
          <div class="flex items-center gap-2">
            <input type="checkbox" v-model="editForm.is_admin" class="w-4 h-4" />
            <label class="text-sm text-gray-700">Администратор</label>
          </div>
          <div class="flex gap-2 pt-2">
            <button type="button" class="btn-secondary flex-1" @click="editUser = null">Отмена</button>
            <button type="submit" class="btn-primary flex-1">Сохранить</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="energyUser" class="fixed inset-0 bg-black/40 z-40 flex items-center justify-center p-4" @click.self="energyUser = null">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg flex flex-col overflow-hidden max-h-[90vh]">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h2 class="font-semibold">⚡ Токены: {{ energyUser.name }}</h2>
            <p class="text-xs text-gray-400 mt-0.5">{{ energyUser.email }}</p>
          </div>
          <button class="text-gray-400 hover:text-gray-600 text-xl" @click="energyUser = null">✕</button>
        </div>
        <div class="flex-1 overflow-y-auto">
          <div v-if="energyData" class="px-6 py-4 border-b border-gray-100">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-gray-500">Текущий баланс</span>
              <span class="text-xl font-bold text-gray-900">{{ energyData.energy_left }}
                <span class="text-sm font-normal text-gray-400">/ {{ energyData.energy_per_week }} в неделю</span>
              </span>
            </div>
            <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all"
                :class="energyPercent > 30 ? 'bg-green-400' : energyPercent > 10 ? 'bg-yellow-400' : 'bg-red-400'"
                :style="{ width: energyPercent + '%' }"
              ></div>
            </div>
          </div>
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="text-sm font-medium text-gray-700 mb-3">Изменить баланс</h3>
            <div class="flex gap-2 mb-2">
              <button class="flex-1 py-2 text-xs rounded-lg border transition-colors"
                :class="adjustMode === 'add' ? 'border-green-400 bg-green-50 text-green-700 font-medium' : 'border-gray-200 text-gray-500'"
                @click="adjustMode = 'add'">+ Начислить</button>
              <button class="flex-1 py-2 text-xs rounded-lg border transition-colors"
                :class="adjustMode === 'sub' ? 'border-red-400 bg-red-50 text-red-700 font-medium' : 'border-gray-200 text-gray-500'"
                @click="adjustMode = 'sub'">− Списать</button>
            </div>
            <div class="flex gap-2">
              <input v-model.number="adjustAmount" type="number" min="1" class="input flex-1" placeholder="Количество токенов" />
              <input v-model="adjustDesc" class="input flex-1" placeholder="Причина (необязательно)" />
              <button class="btn-primary text-sm shrink-0" :disabled="!adjustAmount || adjusting" @click="applyAdjust">
                {{ adjusting ? '...' : 'Применить' }}
              </button>
            </div>
          </div>
          <div class="px-6 py-4">
            <h3 class="text-sm font-medium text-gray-700 mb-3">История расходов</h3>
            <div v-if="!energyData?.transactions?.length" class="text-sm text-gray-400 text-center py-4">Транзакций пока нет</div>
            <div class="space-y-2">
              <div v-for="tx in energyData?.transactions" :key="tx.id"
                class="flex items-start justify-between py-2 border-b border-gray-50 last:border-0">
                <div class="min-w-0">
                  <div class="text-sm text-gray-800">{{ tx.description }}</div>
                  <div class="text-xs text-gray-400 mt-0.5">
                    {{ formatDateTime(tx.created_at) }}
                    <span v-if="tx.tool_name" class="ml-1">· {{ tx.tool_name }}</span>
                  </div>
                </div>
                <span class="text-sm font-semibold ml-4 shrink-0" :class="tx.amount > 0 ? 'text-green-600' : 'text-red-500'">
                  {{ tx.amount > 0 ? '+' : '' }}{{ tx.amount }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { adminApi } from '~/api/admin'
import { useToastStore } from '~/stores/toast'

definePageMeta({ layout: 'admin', middleware: ['auth', 'admin'] })

const toast = useToastStore()
const users = ref([])
const loading = ref(true)
const filterPlan = ref('')
const editUser = ref(null)
const editForm = ref({ name: '', is_admin: false })
const energyUser = ref(null)
const energyData = ref(null)
const adjustMode = ref('add')
const adjustAmount = ref(null)
const adjustDesc = ref('')
const adjusting = ref(false)

const energyPercent = computed(() => {
  if (!energyData.value) return 0
  return Math.min(100, Math.round((energyData.value.energy_left / energyData.value.energy_per_week) * 100))
})

onMounted(() => load())

async function load() {
  loading.value = true
  try {
    const res = await adminApi.getUsers(filterPlan.value ? { plan: filterPlan.value } : {})
    users.value = res.data
  } finally {
    loading.value = false
  }
}

function openEdit(user) {
  editUser.value = user
  editForm.value = { name: user.name, is_admin: user.is_admin }
}

async function saveUser() {
  try {
    const res = await adminApi.updateUser(editUser.value.id, editForm.value)
    const idx = users.value.findIndex((u) => u.id === editUser.value.id)
    if (idx !== -1) users.value[idx] = res.data
    editUser.value = null
    toast.success('Пользователь обновлён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  }
}

async function openEnergy(user) {
  energyUser.value = user
  energyData.value = null
  adjustAmount.value = null
  adjustDesc.value = ''
  adjustMode.value = 'add'
  try {
    const res = await adminApi.getUserEnergy(user.id)
    energyData.value = res.data
  } catch {
    toast.error('Не удалось загрузить баланс')
  }
}

async function applyAdjust() {
  if (!adjustAmount.value) return
  adjusting.value = true
  try {
    const amount = adjustMode.value === 'add' ? Math.abs(adjustAmount.value) : -Math.abs(adjustAmount.value)
    const res = await adminApi.adjustUserEnergy(energyUser.value.id, { amount, description: adjustDesc.value })
    energyData.value = res.data
    adjustAmount.value = null
    adjustDesc.value = ''
    toast.success(`Баланс обновлён: ${amount > 0 ? '+' : ''}${amount} токенов`)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  } finally {
    adjusting.value = false
  }
}

function formatDate(d) { return new Date(d).toLocaleDateString('ru-RU') }
function formatDateTime(d) {
  return new Date(d).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>
