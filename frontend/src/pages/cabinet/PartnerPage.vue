<template>
  <div class="p-8 max-w-4xl">
    <h1 class="text-2xl font-bold text-gray-900 mb-2">Партнёрская программа</h1>
    <p class="text-gray-500 text-sm mb-8">Зарабатывайте токены с каждого запуска ваших инструментов</p>

    <!-- Как это работает -->
    <div class="card p-6 mb-6">
      <h2 class="font-semibold text-gray-800 mb-3">Как это работает</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div class="flex gap-3">
          <div class="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-bold shrink-0">1</div>
          <div><div class="font-medium text-gray-800">Ваш инструмент запускают</div><div class="text-gray-500">Другие пользователи платформы используют ваш инструмент</div></div>
        </div>
        <div class="flex gap-3">
          <div class="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-bold shrink-0">2</div>
          <div><div class="font-medium text-gray-800">Вы получаете 10%</div><div class="text-gray-500">С каждого запуска вам начисляется 10% от стоимости токенов</div></div>
        </div>
        <div class="flex gap-3">
          <div class="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-bold shrink-0">3</div>
          <div><div class="font-medium text-gray-800">Выводите токены</div><div class="text-gray-500">{{ stats?.token_rate ?? 1000 }} токенов = $1. Заявка обрабатывается менеджером</div></div>
        </div>
      </div>
    </div>

    <!-- Баланс -->
    <div class="card p-6 mb-6">
      <div class="flex items-start justify-between">
        <div>
          <div class="text-sm text-gray-500 mb-1">Партнёрский баланс</div>
          <div class="text-3xl font-bold text-gray-900">{{ (stats?.balance ?? 0).toLocaleString('ru') }} <span class="text-lg text-gray-400 font-normal">токенов</span></div>
          <div v-if="stats" class="flex gap-4 mt-2 text-xs text-gray-500">
            <span>Сегодня: <b class="text-green-600">+{{ stats.today_earned }}</b></span>
            <span>Неделя: <b class="text-green-600">+{{ stats.week_earned }}</b></span>
            <span>Месяц: <b class="text-green-600">+{{ stats.month_earned }}</b></span>
          </div>
          <div v-if="stats" class="text-xs text-gray-400 mt-1">≈ ${{ ((stats.balance ?? 0) / (stats.token_rate ?? 1000)).toFixed(2) }}</div>
        </div>
        <button
          class="btn-primary text-sm"
          :disabled="!stats || stats.balance === 0"
          @click="showWithdrawModal = true"
        >Запросить вывод</button>
      </div>
    </div>

    <!-- Мои инструменты -->
    <div class="mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-800">Мои инструменты</h2>
        <a href="https://t.me/ascn_stepan" target="_blank" class="text-xs text-primary-600 hover:underline">+ Добавить инструмент</a>
      </div>
      <div v-if="tools.length === 0" class="card p-8 text-center text-gray-400 text-sm">
        У вас пока нет инструментов в партнёрской программе.<br>
        <a href="https://t.me/ascn_stepan" target="_blank" class="text-primary-600 hover:underline mt-2 inline-block">Связаться с менеджером для добавления</a>
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="tool in tools" :key="tool.id" class="card p-4">
          <div class="font-medium text-gray-900 mb-1">{{ tool.name }}</div>
          <div class="text-xs text-gray-500 mb-3 line-clamp-2">{{ tool.description || 'Нет описания' }}</div>
          <div class="text-xs text-gray-400">Стоимость запуска: <b>{{ tool.energy_cost }} токенов</b> → вам <b class="text-green-600">{{ Math.max(1, Math.floor(tool.energy_cost / 10)) }}</b></div>
        </div>
      </div>
    </div>

    <!-- История транзакций -->
    <div>
      <h2 class="font-semibold text-gray-800 mb-4">История начислений</h2>
      <div v-if="transactions.length === 0" class="card p-6 text-center text-gray-400 text-sm">Транзакций пока нет</div>
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
            <tr v-for="tx in transactions" :key="tx.id">
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

    <!-- Модал вывода -->
    <Teleport to="body">
      <div v-if="showWithdrawModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="showWithdrawModal = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
          <h3 class="font-semibold text-gray-900 mb-4">Запрос на вывод токенов</h3>
          <div class="mb-4">
            <label class="text-xs font-medium text-gray-600 mb-1 block">Количество токенов</label>
            <input v-model.number="withdrawAmount" type="number" :max="stats?.balance" min="1" class="input w-full" placeholder="Введите количество" />
            <div v-if="stats" class="text-xs text-gray-400 mt-1">≈ ${{ ((withdrawAmount || 0) / (stats.token_rate ?? 1000)).toFixed(2) }}</div>
          </div>
          <div class="mb-6">
            <label class="text-xs font-medium text-gray-600 mb-1 block">Комментарий (необязательно)</label>
            <textarea v-model="withdrawComment" class="input w-full" rows="2" placeholder="Например, реквизиты для вывода"></textarea>
          </div>
          <div class="flex gap-2 justify-end">
            <button class="btn-secondary text-sm" @click="showWithdrawModal = false">Отмена</button>
            <button class="btn-primary text-sm" :disabled="withdrawSaving || !withdrawAmount" @click="submitWithdraw">
              {{ withdrawSaving ? 'Отправляю...' : 'Отправить заявку' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { partnerApi } from '@/api/partner'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const stats = ref(null)
const tools = ref([])
const transactions = ref([])
const showWithdrawModal = ref(false)
const withdrawAmount = ref(null)
const withdrawComment = ref('')
const withdrawSaving = ref(false)

onMounted(async () => {
  try {
    const [s, t, tx] = await Promise.all([
      partnerApi.getStats(),
      partnerApi.getTools(),
      partnerApi.getTransactions(),
    ])
    stats.value = s.data
    tools.value = t.data
    transactions.value = tx.data
  } catch (e) {
    toast.error('Ошибка загрузки данных')
  }
})

async function submitWithdraw() {
  if (!withdrawAmount.value || withdrawAmount.value <= 0) return
  withdrawSaving.value = true
  try {
    await partnerApi.requestWithdraw({ amount: withdrawAmount.value, comment: withdrawComment.value || null })
    toast.success('Заявка отправлена! Менеджер свяжется с вами.')
    showWithdrawModal.value = false
    withdrawAmount.value = null
    withdrawComment.value = ''
    const s = await partnerApi.getStats()
    stats.value = s.data
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  } finally {
    withdrawSaving.value = false
  }
}

function formatDate(d) {
  return new Date(d).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>
