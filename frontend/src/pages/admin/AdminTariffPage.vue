<template>
  <div class="p-8 max-w-3xl">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Тарифы ASCN</h1>
        <p class="text-sm text-gray-400 mt-1">Лимиты по каждому тарифу. Синхронизируются при входе пользователя.</p>
      </div>
      <button class="btn-primary text-sm" @click="save" :disabled="saving">
        {{ saving ? 'Сохраняю...' : 'Сохранить' }}
      </button>
    </div>

    <div v-if="loading" class="text-gray-400 text-center py-16">Загрузка...</div>

    <div v-else class="space-y-3">
      <div
        v-for="(row, idx) in mappings"
        :key="idx"
        class="card p-4 grid grid-cols-12 gap-3 items-center"
      >
        <!-- Slug -->
        <div class="col-span-3">
          <label class="text-xs text-gray-400 mb-1 block">Slug (от ASCN)</label>
          <input v-model="row.slug" class="input text-xs font-mono" placeholder="no-code-pro" />
        </div>
        <!-- Название -->
        <div class="col-span-3">
          <label class="text-xs text-gray-400 mb-1 block">Название</label>
          <input v-model="row.name" class="input text-xs" placeholder="No-Code Pro" />
        </div>
        <!-- max_agents -->
        <div class="col-span-2">
          <label class="text-xs text-gray-400 mb-1 block">Агентов</label>
          <input v-model.number="row.max_agents" type="number" min="1" class="input text-xs" />
        </div>
        <!-- max_tools_per_agent -->
        <div class="col-span-2">
          <label class="text-xs text-gray-400 mb-1 block">Инструм./агент</label>
          <input v-model.number="row.max_tools_per_agent" type="number" min="1" class="input text-xs" />
        </div>
        <!-- Удалить -->
        <div class="col-span-2 flex justify-end pt-4">
          <button class="text-xs text-red-400 hover:text-red-600" @click="removeRow(idx)">✕ Удалить</button>
        </div>
      </div>

      <button class="w-full py-3 border-2 border-dashed border-gray-200 text-gray-400 hover:border-primary-300 hover:text-primary-500 rounded-xl text-sm transition-colors" @click="addRow">
        + Добавить тариф
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
          @click="addRowWithSlug(s.slug)"
        >
          {{ s.slug }} <span class="text-gray-400">({{ s.count }})</span>
        </button>
      </div>
    </div>

    <div class="mt-6 p-4 bg-blue-50 rounded-xl text-xs text-blue-600 space-y-1">
      <div class="font-medium">Как работает синхронизация:</div>
      <div>• При каждом входе пользователя — запрашиваем его подписку из ASCN API</div>
      <div>• Slug тарифа из ASCN ищем в таблице выше → берём лимиты агентов и инструментов</div>
      <div>• Токены (energy) берутся из поля <code class="bg-blue-100 px-1 rounded">nocode_credits_count</code> тарифа 1:1</div>
      <div>• Тариф <strong>default</strong> — применяется если у пользователя нет активной подписки</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const mappings = ref([])
const ascnSlugs = ref([])
const loading = ref(true)
const saving = ref(false)

onMounted(async () => {
  try {
    const [mappingsRes, slugsRes] = await Promise.all([
      adminApi.getTariffMappings(),
      adminApi.getAscnSlugs(),
    ])
    mappings.value = mappingsRes.data.map(m => ({ ...m }))
    ascnSlugs.value = slugsRes.data
  } catch {
    toast.error('Ошибка загрузки тарифов')
  } finally {
    loading.value = false
  }
})

function addRow() {
  mappings.value.push({ slug: '', name: '', max_agents: 3, max_tools_per_agent: 3 })
}

function addRowWithSlug(slug) {
  if (mappings.value.some(m => m.slug === slug)) return
  mappings.value.push({ slug, name: slug, max_agents: 3, max_tools_per_agent: 3 })
}

function removeRow(idx) {
  mappings.value.splice(idx, 1)
}

async function save() {
  saving.value = true
  try {
    await adminApi.saveTariffMappings(mappings.value)
    toast.success('Тарифы сохранены')
  } catch {
    toast.error('Ошибка сохранения')
  } finally {
    saving.value = false
  }
}
</script>
