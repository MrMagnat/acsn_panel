<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">База знаний</h1>
        <p class="text-gray-500 text-sm mt-1">Ваши таблицы с данными для использования в инструментах</p>
      </div>
      <button class="btn-primary" @click="showCreate = true">+ Создать базу</button>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <div v-else-if="!bases.length" class="text-center py-16 text-gray-400">
      <div class="text-4xl mb-3">🗃️</div>
      <p class="font-medium">Нет баз данных</p>
      <p class="text-sm mt-1">Создайте первую базу и загрузите контакты, списки или любые данные</p>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="base in bases"
        :key="base.id"
        class="card p-5 cursor-pointer hover:shadow-md transition-shadow group"
        @click="router.push(`/cabinet/knowledge-base/${base.id}`)"
      >
        <div class="flex items-start justify-between">
          <div class="text-3xl mb-3">🗂️</div>
          <button
            class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all text-sm"
            @click.stop="deleteBase(base)"
          >✕</button>
        </div>
        <h3 class="font-semibold text-gray-900">{{ base.name }}</h3>
        <p class="text-xs text-gray-400 mt-1">{{ base.fields_count }} колонок</p>
        <p class="text-xs text-gray-400">{{ formatDate(base.created_at) }}</p>
      </div>
    </div>

    <!-- Модал создания -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/40 z-40 flex items-center justify-center p-4" @click.self="showCreate = false">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
        <h2 class="font-semibold mb-4">Новая база данных</h2>
        <form @submit.prevent="createBase">
          <label class="label">Название</label>
          <input v-model="newName" class="input mb-4" placeholder="Контакты клиентов" autofocus required />
          <div class="flex gap-2">
            <button type="button" class="btn-secondary flex-1" @click="showCreate = false">Отмена</button>
            <button type="submit" class="btn-primary flex-1" :disabled="creating">
              {{ creating ? '...' : 'Создать' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { kbApi } from '@/api/knowledge-base'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const toast = useToastStore()
const bases = ref([])
const loading = ref(true)
const showCreate = ref(false)
const newName = ref('')
const creating = ref(false)

onMounted(load)

async function load() {
  loading.value = true
  try {
    const res = await kbApi.list()
    bases.value = res.data
  } finally {
    loading.value = false
  }
}

async function createBase() {
  if (!newName.value.trim()) return
  creating.value = true
  try {
    const res = await kbApi.create(newName.value.trim())
    showCreate.value = false
    newName.value = ''
    router.push(`/cabinet/knowledge-base/${res.data.id}`)
  } catch {
    toast.error('Ошибка создания')
  } finally {
    creating.value = false
  }
}

async function deleteBase(base) {
  if (!confirm(`Удалить базу «${base.name}»? Все данные будут потеряны.`)) return
  try {
    await kbApi.delete(base.id)
    bases.value = bases.value.filter((b) => b.id !== base.id)
    toast.success('База удалена')
  } catch {
    toast.error('Ошибка удаления')
  }
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('ru-RU')
}
</script>
