<template>
  <div class="p-8 max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">ASCN AI — конфигурация</h1>

    <div v-if="loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <template v-else>
      <!-- OpenRouter ключ -->
      <div class="card p-6 mb-6">
        <h2 class="font-semibold text-gray-700 mb-4">OpenRouter API ключ</h2>
        <p class="text-xs text-gray-400 mb-3">Этот ключ используется когда пользователь выбирает оператора «ASCN». Пользователи его не видят.</p>
        <div class="relative">
          <input
            v-model="config.openrouter_key"
            :type="showKey ? 'text' : 'password'"
            class="input pr-10"
            placeholder="sk-or-v1-..."
          />
          <button class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400" @click="showKey = !showKey">
            {{ showKey ? '🙈' : '👁' }}
          </button>
        </div>
      </div>

      <!-- Модели и цены -->
      <div class="card p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="font-semibold text-gray-700">Модели и цены</h2>
            <p class="text-xs text-gray-400 mt-0.5">Цены в центах (100 = $1.00). Списывается за каждое сообщение.</p>
          </div>
          <button class="btn-secondary text-xs" @click="addModel">+ Модель</button>
        </div>

        <div class="space-y-3">
          <div v-for="(model, idx) in config.models" :key="idx" class="p-3 rounded-lg bg-gray-50 border border-gray-100">
            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="text-xs text-gray-500">OpenRouter ID</label>
                <input v-model="model.id" class="input text-xs mt-0.5 font-mono" placeholder="openai/gpt-4o-mini" />
              </div>
              <div>
                <label class="text-xs text-gray-500">Название для пользователя</label>
                <input v-model="model.name" class="input text-xs mt-0.5" placeholder="GPT-4o mini" />
              </div>
              <div>
                <label class="text-xs text-gray-500">Цена (центы/сообщ.)</label>
                <div class="flex gap-2 mt-0.5">
                  <input v-model.number="model.price_usd" type="number" min="0" class="input text-xs flex-1" />
                  <span class="text-xs text-gray-400 self-center">${{ (model.price_usd / 100).toFixed(2) }}</span>
                  <button class="text-red-400 hover:text-red-600 text-xs" @click="config.models.splice(idx, 1)">✕</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <button class="btn-primary" :disabled="saving" @click="save">
        {{ saving ? 'Сохраняю...' : 'Сохранить' }}
      </button>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { useToastStore } from '@/stores/toast'
import http from '@/api/http'

const toast = useToastStore()
const loading = ref(true)
const saving = ref(false)
const showKey = ref(false)

const config = ref({ openrouter_key: '', models: [] })

onMounted(async () => {
  try {
    const res = await http.get('/admin/ascn-config')
    config.value = res.data
  } finally {
    loading.value = false
  }
})

function addModel() {
  config.value.models.push({ id: '', name: '', price_usd: 2 })
}

async function save() {
  saving.value = true
  try {
    await http.put('/admin/ascn-config', config.value)
    toast.success('Конфигурация сохранена')
  } catch {
    toast.error('Ошибка сохранения')
  } finally {
    saving.value = false
  }
}
</script>
