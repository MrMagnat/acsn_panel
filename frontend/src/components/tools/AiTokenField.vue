<template>
  <div class="space-y-2">
    <!-- Mode toggle -->
    <div class="flex gap-2">
      <button
        type="button"
        class="flex-1 py-1.5 text-xs rounded-lg border transition-colors"
        :class="mode === 'ascn' ? 'border-orange-400 bg-orange-50 text-orange-700 font-medium' : 'border-gray-200 text-gray-500 hover:border-gray-300'"
        @click="setMode('ascn')"
      >✦ ASCN (встроенный)</button>
      <button
        type="button"
        class="flex-1 py-1.5 text-xs rounded-lg border transition-colors"
        :class="mode === 'own' ? 'border-primary-400 bg-primary-50 text-primary-700 font-medium' : 'border-gray-200 text-gray-500 hover:border-gray-300'"
        @click="setMode('own')"
      >🔑 Свой ключ</button>
    </div>

    <!-- ASCN mode -->
    <div v-if="mode === 'ascn'">
      <select class="input text-sm" :value="localModel" @change="localModel = $event.target.value; emitValue()">
        <option value="">— выберите модель —</option>
        <option v-for="m in ascnModels" :key="m.id" :value="m.id">
          {{ m.name }} · ${{ (m.price_usd / 10000).toFixed(4).replace(/\.?0+$/, '') }}/сообщ.
        </option>
      </select>
    </div>

    <!-- Own key mode -->
    <div v-else class="space-y-2">
      <input
        :value="localOperator"
        class="input text-xs"
        placeholder="Оператор (напр. openrouter)"
        @input="localOperator = $event.target.value; emitValue()"
      />
      <input
        :value="localModel"
        class="input text-xs"
        placeholder="Модель (напр. openai/gpt-4o-mini)"
        @input="localModel = $event.target.value; emitValue()"
      />
      <input
        :value="localToken"
        class="input text-xs font-mono"
        placeholder="API ключ (sk-or-...)"
        type="password"
        @input="localToken = $event.target.value; emitValue()"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  modelValue: { type: [Object, String], default: null },
})
const emit = defineEmits(['update:modelValue'])

const mode = ref('ascn')
const localModel = ref('')
const localOperator = ref('openrouter')
const localToken = ref('')
const ascnModels = ref([])

onMounted(async () => {
  try {
    const { default: http } = await import('@/api/http')
    const res = await http.get('/onboarding/ascn-models')
    ascnModels.value = res.data
  } catch {}
  initFromValue(props.modelValue)
})

watch(() => props.modelValue, (v) => initFromValue(v), { deep: true })

function initFromValue(v) {
  if (!v) return
  const obj = typeof v === 'string' ? tryParse(v) : v
  if (!obj || typeof obj !== 'object') return
  if (obj.operator === 'ascn' || obj.token === '__ascn__') {
    mode.value = 'ascn'
    localModel.value = obj.model || ''
  } else {
    mode.value = 'own'
    localOperator.value = obj.operator || 'openrouter'
    localModel.value = obj.model || ''
    localToken.value = obj.token || ''
  }
}

function tryParse(s) {
  try { return JSON.parse(s) } catch { return null }
}

function setMode(m) {
  mode.value = m
  emitValue()
}

function emitValue() {
  if (mode.value === 'ascn') {
    emit('update:modelValue', { operator: 'ascn', model: localModel.value, token: '__ascn__' })
  } else {
    emit('update:modelValue', { operator: localOperator.value, model: localModel.value, token: localToken.value })
  }
}
</script>
