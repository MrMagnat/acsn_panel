<template>
  <div class="text-xs text-gray-600">
    <div v-if="parsed?.error" class="text-red-500">{{ parsed.error }}</div>
    <div v-else-if="parsed?.message" class="text-gray-700">{{ parsed.message }}</div>
    <div v-else-if="parsed?.result && typeof parsed.result === 'string'" class="text-gray-700 line-clamp-3">{{ parsed.result }}</div>
    <div v-else-if="parsed" class="space-y-0.5">
      <div v-for="(val, key) in previewEntries" :key="key" class="flex gap-1">
        <span class="text-gray-400 shrink-0">{{ key }}:</span>
        <span class="text-gray-700 truncate">{{ formatVal(val) }}</span>
      </div>
      <div v-if="totalKeys > 3" class="text-gray-400">...ещё {{ totalKeys - 3 }} полей</div>
    </div>
    <div v-else class="text-gray-400 italic">нет данных</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ resultJson: { type: String, default: null } })

const parsed = computed(() => {
  if (!props.resultJson) return null
  try { return JSON.parse(props.resultJson) } catch { return { result: props.resultJson } }
})

const previewEntries = computed(() => {
  if (!parsed.value || typeof parsed.value !== 'object') return {}
  return Object.fromEntries(Object.entries(parsed.value).slice(0, 3))
})

const totalKeys = computed(() => {
  if (!parsed.value || typeof parsed.value !== 'object') return 0
  return Object.keys(parsed.value).length
})

function formatVal(v) {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v).slice(0, 60)
  return String(v).slice(0, 80)
}
</script>
