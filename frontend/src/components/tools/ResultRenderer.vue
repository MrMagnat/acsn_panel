<template>
  <div class="result-renderer">

    <!-- Ошибка -->
    <div v-if="isError" class="flex items-start gap-2 text-red-600 bg-red-50 rounded-lg p-3">
      <span class="text-lg leading-none mt-0.5">❌</span>
      <div class="text-sm">{{ errorMessage }}</div>
    </div>

    <!-- Остановлено пользователем -->
    <div v-else-if="isCancelled" class="flex items-center gap-2 text-gray-600 bg-gray-50 rounded-lg p-3">
      <span class="text-lg leading-none">⏹</span>
      <span class="text-sm">Процесс остановлен пользователем</span>
    </div>

    <!-- Статус "запущен / в процессе" -->
    <div v-else-if="isStarted" class="flex items-center gap-2 text-yellow-700 bg-yellow-50 rounded-lg p-3">
      <span class="inline-block w-4 h-4 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin"></span>
      <span class="text-sm">Задача запущена, ожидаем результат...</span>
    </div>

    <!-- Числовые метрики (объект из чисел) -->
    <div v-else-if="isMetrics" class="grid grid-cols-2 gap-2">
      <div
        v-for="(value, key) in metricsData"
        :key="key"
        class="bg-gray-50 rounded-lg p-3 text-center"
      >
        <div class="text-2xl font-bold" :class="metricColor(key, value)">{{ value }}</div>
        <div class="text-xs text-gray-500 mt-0.5">{{ formatKey(key) }}</div>
      </div>
    </div>

    <!-- Массив объектов → таблица / карточки -->
    <div v-else-if="isArray">
      <!-- Если элементов <= 3, показываем карточками -->
      <div v-if="parsed.length <= 3" class="space-y-2">
        <div
          v-for="(item, i) in parsed"
          :key="i"
          class="bg-gray-50 rounded-lg p-3 text-sm"
        >
          <div v-for="(v, k) in item" :key="k" class="flex justify-between gap-2 py-0.5 border-b border-gray-100 last:border-0">
            <span class="text-gray-500 shrink-0">{{ formatKey(k) }}</span>
            <span class="font-medium text-gray-800 text-right truncate">{{ formatValue(v) }}</span>
          </div>
        </div>
      </div>
      <!-- Больше 3 элементов → компактный список -->
      <div v-else class="space-y-1 max-h-48 overflow-y-auto">
        <div
          v-for="(item, i) in parsed"
          :key="i"
          class="flex items-center gap-2 text-sm px-2 py-1.5 rounded hover:bg-gray-50"
        >
          <span class="text-gray-400 text-xs w-5 text-right shrink-0">{{ i + 1 }}</span>
          <span class="text-gray-800 truncate">{{ itemSummary(item) }}</span>
        </div>
        <p class="text-xs text-gray-400 text-center pt-1">Всего: {{ parsed.length }}</p>
      </div>
    </div>

    <!-- Текстовый результат -->
    <div v-else-if="isText" class="text-sm text-gray-800 bg-gray-50 rounded-lg p-3 whitespace-pre-wrap">
      {{ textContent }}
    </div>

    <!-- Объект с ключами — таблица key:value -->
    <div v-else-if="isObject" class="space-y-1">
      <div
        v-for="(value, key) in parsed"
        :key="key"
        class="flex justify-between gap-3 text-sm py-1.5 px-2 rounded hover:bg-gray-50 border-b border-gray-50 last:border-0"
      >
        <span class="text-gray-500 shrink-0 capitalize">{{ formatKey(key) }}</span>
        <span class="font-medium text-gray-800 text-right truncate max-w-[60%]">
          <!-- URL → ссылка -->
          <a v-if="isUrl(value)" :href="value" target="_blank" class="text-primary-600 underline truncate">{{ value }}</a>
          <!-- Булевое -->
          <span v-else-if="typeof value === 'boolean'" :class="value ? 'text-green-600' : 'text-red-500'">
            {{ value ? 'Да' : 'Нет' }}
          </span>
          <!-- Обычное значение -->
          <span v-else>{{ formatValue(value) }}</span>
        </span>
      </div>
    </div>

    <!-- Fallback: красивый JSON -->
    <pre v-else class="text-xs bg-gray-50 rounded-lg p-3 overflow-auto max-h-40 text-gray-700">{{ prettyJson }}</pre>

  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  resultJson: { type: String, default: null },
  status: { type: String, default: 'running' }, // running / success / error
})

// Парсим JSON
const parsed = computed(() => {
  if (!props.resultJson) return null
  try { return JSON.parse(props.resultJson) } catch { return props.resultJson }
})

const isError = computed(() => props.status === 'error')
const isCancelled = computed(() => props.status === 'cancelled')
const isStarted = computed(() => props.status === 'running')

const errorMessage = computed(() => {
  if (!parsed.value) return 'Неизвестная ошибка'
  if (typeof parsed.value === 'string') return parsed.value
  return parsed.value?.error || parsed.value?.message || JSON.stringify(parsed.value)
})

// Определяем тип данных
const isArray   = computed(() => Array.isArray(parsed.value) && parsed.value.length > 0)
const isObject  = computed(() => parsed.value && typeof parsed.value === 'object' && !Array.isArray(parsed.value))
const isText    = computed(() => typeof parsed.value === 'string' && parsed.value.length > 0)

// Метрики: объект где большинство значений — числа и нет вложенных объектов
const metricsData = computed(() => {
  if (!isObject.value) return {}
  const entries = Object.entries(parsed.value)
  const numericEntries = entries.filter(([, v]) => typeof v === 'number' || (typeof v === 'string' && !isNaN(v) && v !== ''))
  if (numericEntries.length >= 2 && numericEntries.length >= entries.length * 0.6) {
    return Object.fromEntries(numericEntries)
  }
  return {}
})
const isMetrics = computed(() => Object.keys(metricsData.value).length >= 2)

const textContent = computed(() => {
  if (!isObject.value) return parsed.value
  const txt = parsed.value?.text || parsed.value?.content || parsed.value?.message || parsed.value?.result
  return typeof txt === 'string' ? txt : null
})

const prettyJson = computed(() => JSON.stringify(parsed.value, null, 2))

// Утилиты
function formatKey(key) {
  return String(key).replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')
}

function formatValue(v) {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

function isUrl(v) {
  return typeof v === 'string' && (v.startsWith('http://') || v.startsWith('https://'))
}

function metricColor(key, value) {
  const k = key.toLowerCase()
  if (k.includes('error') || k.includes('fail') || k.includes('failed')) return 'text-red-600'
  if (k.includes('success') || k.includes('sent') || k.includes('done')) return 'text-green-600'
  return 'text-primary-700'
}

function itemSummary(item) {
  if (typeof item !== 'object') return String(item)
  const val = item.name || item.title || item.text || item.message || item.username || item.email
  return val ? String(val) : Object.values(item).slice(0, 2).join(' · ')
}
</script>
