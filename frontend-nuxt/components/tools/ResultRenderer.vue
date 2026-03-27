<template>
  <div class="result-renderer">

    <!-- Ошибка -->
    <div v-if="isError" class="flex items-start gap-2 text-red-600 bg-red-50 rounded-lg p-3">
      <span class="text-lg leading-none mt-0.5">❌</span>
      <div class="text-sm">{{ errorMessage }}</div>
    </div>

    <!-- Остановлено -->
    <div v-else-if="isCancelled" class="flex items-center gap-2 text-gray-600 bg-gray-50 rounded-lg p-3">
      <span class="text-lg leading-none">⏹</span>
      <span class="text-sm">Процесс остановлен пользователем</span>
    </div>

    <!-- Выполняется -->
    <div v-else-if="isStarted" class="flex items-center gap-2 text-yellow-700 bg-yellow-50 rounded-lg p-3">
      <span class="inline-block w-4 h-4 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin"></span>
      <span class="text-sm">Задача запущена, ожидаем результат...</span>
    </div>

    <!-- Числовые метрики -->
    <div v-else-if="isMetrics" class="space-y-3">
      <div class="grid grid-cols-2 gap-2">
        <div
          v-for="(value, key) in metricsData"
          :key="key"
          class="bg-gray-50 rounded-lg p-3 text-center"
        >
          <div class="text-2xl font-bold" :class="metricColor(key)">{{ value }}</div>
          <div class="text-xs text-gray-500 mt-0.5">{{ formatKey(key) }}</div>
        </div>
      </div>
      <div v-if="nonMetricEntries.length" class="space-y-0.5">
        <ValueRow
          v-for="[k, v] in nonMetricEntries"
          :key="k"
          :label="formatKey(k)"
          :value="v"
          :depth="0"
        />
      </div>
    </div>

    <!-- Массив -->
    <div v-else-if="isArray" class="space-y-2">
      <div class="border border-gray-100 rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-3 py-1.5 text-xs text-gray-400 font-medium border-b border-gray-100">
          #1 из {{ parsed.length }}
        </div>
        <div class="p-3">
          <template v-if="isPlainObject(parsed[0])">
            <ValueRow
              v-for="[k, v] in Object.entries(parsed[0])"
              :key="k"
              :label="formatKey(k)"
              :value="v"
              :depth="0"
            />
          </template>
          <span v-else class="text-sm text-gray-800">{{ formatValue(parsed[0]) }}</span>
        </div>
      </div>

      <template v-if="parsed.length > 1">
        <button
          v-if="!arrayExpanded"
          class="w-full text-sm text-primary-600 bg-primary-50 hover:bg-primary-100 rounded-lg py-2 transition-colors"
          @click="arrayExpanded = true"
        >
          Показать ещё +{{ parsed.length - 1 }} {{ itemsLabel(parsed.length - 1) }}
        </button>

        <template v-else>
          <div
            v-for="(item, i) in parsed.slice(1)"
            :key="i"
            class="border border-gray-100 rounded-lg overflow-hidden"
          >
            <div class="bg-gray-50 px-3 py-1.5 text-xs text-gray-400 font-medium border-b border-gray-100">
              #{{ i + 2 }}
            </div>
            <div class="p-3">
              <template v-if="isPlainObject(item)">
                <ValueRow
                  v-for="[k, v] in Object.entries(item)"
                  :key="k"
                  :label="formatKey(k)"
                  :value="v"
                  :depth="0"
                />
              </template>
              <span v-else class="text-sm text-gray-800">{{ formatValue(item) }}</span>
            </div>
          </div>
          <button
            class="w-full text-xs text-gray-400 hover:text-gray-600 py-1.5 transition-colors"
            @click="arrayExpanded = false"
          >
            Свернуть ↑
          </button>
        </template>
      </template>
    </div>

    <!-- Текст -->
    <div v-else-if="isText">
      <div class="text-sm text-gray-800 bg-gray-50 rounded-lg p-3 whitespace-pre-wrap"
           :class="isLongText && !textExpanded ? 'line-clamp-6' : ''">
        {{ textContent }}
      </div>
      <div v-if="isLongText" class="flex gap-2 mt-2">
        <button
          class="text-xs text-primary-600 hover:underline"
          @click="textPopup = true"
        >
          Читать полностью →
        </button>
      </div>
    </div>

    <!-- Объект -->
    <div v-else-if="isObject" class="space-y-0.5">
      <ValueRow
        v-for="[k, v] in Object.entries(parsed)"
        :key="k"
        :label="formatKey(k)"
        :value="v"
        :depth="0"
      />
    </div>

    <!-- Fallback JSON -->
    <pre v-else class="text-xs bg-gray-50 rounded-lg p-3 overflow-auto max-h-40 text-gray-700">{{ prettyJson }}</pre>

  </div>

  <!-- Попап с полным текстом -->
  <Teleport to="body">
    <div v-if="textPopup" class="fixed inset-0 bg-black/40 z-[100] flex items-center justify-center p-4" @click.self="textPopup = false">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg flex flex-col" style="max-height: 80vh;">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
          <h3 class="font-semibold text-gray-900 text-sm">Результат</h3>
          <button class="text-gray-400 hover:text-gray-600" @click="textPopup = false">✕</button>
        </div>
        <div class="px-6 py-4 overflow-y-auto flex-1">
          <p class="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">{{ textContent }}</p>
        </div>
        <div class="px-6 pb-4 flex justify-end gap-2 shrink-0 border-t border-gray-100 pt-3">
          <button class="btn-secondary text-sm" @click="copyText">{{ copied ? '✅ Скопировано' : '📋 Копировать' }}</button>
          <button class="btn-primary text-sm" @click="textPopup = false">Закрыть</button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Попап для длинных строк внутри объектов/массивов -->
  <Teleport to="body">
    <div v-if="longTextPopup" class="fixed inset-0 bg-black/40 z-[100] flex items-center justify-center p-4" @click.self="longTextPopup = false">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg flex flex-col" style="max-height: 80vh;">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
          <h3 class="font-semibold text-gray-900 text-sm">{{ longTextLabel }}</h3>
          <button class="text-gray-400 hover:text-gray-600" @click="longTextPopup = false">✕</button>
        </div>
        <div class="px-6 py-4 overflow-y-auto flex-1">
          <p class="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">{{ longTextValue }}</p>
        </div>
        <div class="px-6 pb-4 flex justify-end gap-2 shrink-0 border-t border-gray-100 pt-3">
          <button class="btn-secondary text-sm" @click="copyLongText">{{ longTextCopied ? '✅ Скопировано' : '📋 Копировать' }}</button>
          <button class="btn-primary text-sm" @click="longTextPopup = false">Закрыть</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref, defineComponent, h, resolveComponent } from 'vue'

const longTextLabel = ref('')
const longTextValue = ref('')
const longTextPopup = ref(false)
const longTextCopied = ref(false)

function openLongText(label, value) {
  longTextLabel.value = label
  longTextValue.value = value
  longTextPopup.value = true
  longTextCopied.value = false
}

async function copyLongText() {
  try {
    await copyToClipboard(longTextValue.value)
    longTextCopied.value = true
    setTimeout(() => { longTextCopied.value = false }, 2000)
  } catch {}
}

const ValueRow = defineComponent({
  name: 'ValueRow',
  props: {
    label: String,
    value: { default: null },
    depth: { type: Number, default: 0 },
  },
  setup(props) {
    const expanded = ref(true)
    const arrayExpanded = ref(false)

    const isObj = computed(() => props.value && typeof props.value === 'object' && !Array.isArray(props.value))
    const isArr = computed(() => Array.isArray(props.value))
    const isPrim = computed(() => !isObj.value && !isArr.value)

    function fmtPrim(v) {
      if (v === null || v === undefined) return '—'
      if (typeof v === 'boolean') return v ? 'Да' : 'Нет'
      return String(v)
    }
    function isUrl(v) {
      return typeof v === 'string' && (v.startsWith('http://') || v.startsWith('https://'))
    }
    function metricColor(key) {
      const k = String(key).toLowerCase()
      if (k.includes('error') || k.includes('fail')) return 'text-red-600'
      if (k.includes('success') || k.includes('sent') || k.includes('done') || k.includes('ok')) return 'text-green-600'
      return 'text-primary-700'
    }
    function formatKey(key) {
      return String(key).replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')
    }

    const indent = computed(() => props.depth * 12)

    return () => {
      const VR = resolveComponent('ValueRow')
      const pad = `${indent.value}px`

      if (isPrim.value) {
        const strVal = fmtPrim(props.value)
        const isLong = typeof props.value === 'string' && props.value.length > 150
        return h('div', {
          class: 'text-sm py-1.5 px-2 rounded hover:bg-gray-50 border-b border-gray-50 last:border-0',
          style: { paddingLeft: pad },
        }, [
          h('div', { class: 'flex justify-between gap-3 items-start' }, [
            h('span', { class: 'text-gray-500 shrink-0' }, props.label),
            isUrl(props.value)
              ? h('a', { href: props.value, target: '_blank', class: 'text-primary-600 underline truncate max-w-[60%] text-right' }, props.value)
              : isLong
                ? h('div', { class: 'flex flex-col items-end gap-1 max-w-[65%]' }, [
                    h('span', { class: 'font-medium text-gray-800 text-right text-xs line-clamp-2' }, strVal.slice(0, 120) + '...'),
                    h('button', {
                      class: 'text-xs text-primary-600 hover:underline whitespace-nowrap',
                      onClick: () => openLongText(props.label, props.value),
                    }, '📖 Читать полностью'),
                  ])
                : h('span', { class: 'font-medium text-gray-800 text-right truncate max-w-[60%]' }, strVal),
          ]),
        ])
      }

      if (isObj.value) {
        const entries = Object.entries(props.value)
        return h('div', { style: { paddingLeft: pad } }, [
          h('div', {
            class: 'flex items-center gap-1 text-sm py-1 px-2 cursor-pointer select-none hover:bg-gray-50 rounded',
            onClick: () => { expanded.value = !expanded.value },
          }, [
            h('span', { class: 'text-gray-400 text-xs w-3' }, expanded.value ? '▾' : '▸'),
            h('span', { class: 'text-gray-600 font-medium' }, props.label),
            h('span', { class: 'text-xs text-gray-400 ml-1' }, `{${entries.length}}`),
          ]),
          expanded.value
            ? h('div', { class: 'ml-2 border-l-2 border-gray-100 pl-2' },
                entries.map(([k, v]) =>
                  h(VR, { key: k, label: formatKey(k), value: v, depth: 0 })
                )
              )
            : null,
        ])
      }

      if (isArr.value) {
        const arr = props.value
        return h('div', { style: { paddingLeft: pad } }, [
          h('div', {
            class: 'flex items-center gap-1 text-sm py-1 px-2 cursor-pointer select-none hover:bg-gray-50 rounded',
            onClick: () => { expanded.value = !expanded.value },
          }, [
            h('span', { class: 'text-gray-400 text-xs w-3' }, expanded.value ? '▾' : '▸'),
            h('span', { class: 'text-gray-600 font-medium' }, props.label),
            h('span', { class: 'text-xs text-gray-400 ml-1' }, `[${arr.length}]`),
          ]),
          expanded.value
            ? h('div', { class: 'ml-2 border-l-2 border-gray-100 pl-2 space-y-1' }, [
                h('div', { class: 'text-xs text-gray-400 pt-1 pb-0.5 font-medium' }, '#1'),
                typeof arr[0] === 'object' && arr[0] !== null
                  ? h('div', {}, Object.entries(arr[0]).map(([k, v]) => h(VR, { key: k, label: formatKey(k), value: v, depth: 0 })))
                  : h('span', { class: 'text-sm text-gray-800' }, fmtPrim(arr[0])),
                arr.length > 1
                  ? [
                      !arrayExpanded.value
                        ? h('button', {
                            class: 'text-xs text-primary-600 bg-primary-50 hover:bg-primary-100 rounded px-2 py-1 mt-1 transition-colors',
                            onClick: (e) => { e.stopPropagation(); arrayExpanded.value = true },
                          }, `Показать ещё +${arr.length - 1}`)
                        : [
                            ...arr.slice(1).map((item, i) =>
                              h('div', { key: i }, [
                                h('div', { class: 'text-xs text-gray-400 pt-2 pb-0.5 font-medium' }, `#${i + 2}`),
                                typeof item === 'object' && item !== null
                                  ? h('div', {}, Object.entries(item).map(([k, v]) => h(VR, { key: k, label: formatKey(k), value: v, depth: 0 })))
                                  : h('span', { class: 'text-sm text-gray-800' }, fmtPrim(item)),
                              ])
                            ),
                            h('button', {
                              class: 'text-xs text-gray-400 hover:text-gray-600 mt-1 px-2 py-1 transition-colors',
                              onClick: (e) => { e.stopPropagation(); arrayExpanded.value = false },
                            }, 'Свернуть ↑'),
                          ],
                    ]
                  : null,
              ])
            : null,
        ])
      }

      return null
    }
  },
})

const props = defineProps({
  resultJson: { type: String, default: null },
  status: { type: String, default: 'running' },
})

const arrayExpanded = ref(false)
const textExpanded = ref(false)
const textPopup = ref(false)
const copied = ref(false)

const parsed = computed(() => {
  if (!props.resultJson) return null
  try { return JSON.parse(props.resultJson) } catch { return props.resultJson }
})

const isError     = computed(() => props.status === 'error')
const isCancelled = computed(() => props.status === 'cancelled')
const isStarted   = computed(() => props.status === 'running')
const isArray     = computed(() => Array.isArray(parsed.value) && parsed.value.length > 0)
const isObject    = computed(() => parsed.value && typeof parsed.value === 'object' && !Array.isArray(parsed.value))
const isText      = computed(() => typeof parsed.value === 'string' && parsed.value.length > 0)

const metricsData = computed(() => {
  if (!isObject.value) return {}
  const entries = Object.entries(parsed.value)
  const num = entries.filter(([, v]) => typeof v === 'number' || (typeof v === 'string' && !isNaN(v) && v !== ''))
  if (num.length >= 2 && num.length >= entries.length * 0.5) return Object.fromEntries(num)
  return {}
})
const isMetrics = computed(() => Object.keys(metricsData.value).length >= 2)

const nonMetricEntries = computed(() => {
  if (!isMetrics.value || !isObject.value) return []
  const metricKeys = new Set(Object.keys(metricsData.value))
  return Object.entries(parsed.value).filter(([k]) => !metricKeys.has(k))
})

const textContent = computed(() => {
  if (isText.value) return parsed.value
  if (isObject.value) {
    const txt = parsed.value?.text || parsed.value?.content || parsed.value?.message
    return typeof txt === 'string' ? txt : null
  }
  return null
})

const errorMessage = computed(() => {
  if (!parsed.value) return 'Неизвестная ошибка'
  if (typeof parsed.value === 'string') return parsed.value
  return parsed.value?.error || parsed.value?.message || JSON.stringify(parsed.value)
})

const prettyJson = computed(() => JSON.stringify(parsed.value, null, 2))

function formatKey(key) {
  return String(key).replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')
}
function formatValue(v) {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}
function isPlainObject(v) {
  return v && typeof v === 'object' && !Array.isArray(v)
}
function metricColor(key) {
  const k = String(key).toLowerCase()
  if (k.includes('error') || k.includes('fail')) return 'text-red-600'
  if (k.includes('success') || k.includes('sent') || k.includes('done')) return 'text-green-600'
  return 'text-primary-700'
}
const isLongText = computed(() => typeof textContent.value === 'string' && textContent.value.length > 300)

function copyToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text)
  }
  const el = document.createElement('textarea')
  el.value = text
  el.style.cssText = 'position:fixed;opacity:0;pointer-events:none'
  document.body.appendChild(el)
  el.select()
  document.execCommand('copy')
  document.body.removeChild(el)
  return Promise.resolve()
}

async function copyText() {
  try {
    await copyToClipboard(textContent.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch { /* ignore */ }
}

function itemsLabel(n) {
  if (n % 10 === 1 && n % 100 !== 11) return 'запись'
  if ([2,3,4].includes(n % 10) && ![12,13,14].includes(n % 100)) return 'записи'
  return 'записей'
}
</script>
