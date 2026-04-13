<template>
  <div class="p-8 max-w-4xl">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Скиллы</h1>
        <p class="text-sm text-gray-400 mt-1">Каталог знаний и поведений — добавляются агентам и встраиваются в чат</p>
      </div>
      <button class="btn-primary text-sm" @click="openCreate">+ Создать скилл</button>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <div v-else-if="!skills.length" class="text-center py-16 text-gray-400">
      <div class="text-4xl mb-3">✨</div>
      <div>Скиллов пока нет</div>
      <div class="text-sm mt-1">Создайте первый скилл</div>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="skill in skills"
        :key="skill.id"
        class="card p-4 flex items-start gap-4"
      >
        <div class="text-3xl shrink-0 w-10 text-center">{{ skill.icon }}</div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-0.5">
            <span class="font-semibold text-gray-900">{{ skill.name }}</span>
            <span class="text-xs font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{{ skill.slug }}</span>
            <span v-if="skill.category" class="text-xs px-1.5 py-0.5 rounded-full bg-purple-50 text-purple-600 border border-purple-100">{{ skill.category }}</span>
            <span v-if="!skill.is_active" class="text-xs px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-400">неактивен</span>
          </div>
          <p v-if="skill.description" class="text-xs text-gray-500 mb-1">{{ skill.description }}</p>
          <p class="text-xs text-gray-400 line-clamp-2">{{ skill.content }}</p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button class="text-xs text-primary-600 hover:underline" @click="openEdit(skill)">Редактировать</button>
          <button class="text-xs text-red-400 hover:text-red-600" @click="deleteSkill(skill)">Удалить</button>
        </div>
      </div>
    </div>

    <!-- Модал создания/редактирования -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="showModal = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl flex flex-col max-h-[90vh]">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
            <h3 class="font-semibold text-gray-900">{{ editingSkill?.id ? 'Редактировать скилл' : 'Создать скилл' }}</h3>
            <button class="text-gray-400 hover:text-gray-600" @click="showModal = false">✕</button>
          </div>
          <div class="px-6 py-4 space-y-3 overflow-y-auto flex-1">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="label">Название *</label>
                <input v-model="form.name" class="input text-sm" placeholder="Эксперт по продажам" />
              </div>
              <div>
                <label class="label">Slug *</label>
                <input v-model="form.slug" class="input text-sm font-mono" placeholder="sales-expert" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="label">Иконка (эмодзи)</label>
                <input v-model="form.icon" class="input text-sm" placeholder="✨" />
              </div>
              <div>
                <label class="label">Категория</label>
                <input v-model="form.category" class="input text-sm" placeholder="Продажи, Поддержка..." />
              </div>
            </div>
            <div>
              <label class="label">Описание (видит пользователь)</label>
              <input v-model="form.description" class="input text-sm" placeholder="Краткое описание..." />
            </div>
            <div>
              <label class="label">Контент <span class="text-gray-400 font-normal">(инжектируется в system prompt агента)</span></label>
              <textarea
                v-model="form.content"
                class="input text-sm resize-none font-mono"
                rows="10"
                placeholder="Ты — эксперт по продажам. Ты умеешь..."
              />
              <p class="text-xs text-gray-400 mt-1">Этот текст добавится в системный промпт агента после добавления скилла</p>
            </div>
            <div class="flex items-center gap-2">
              <input type="checkbox" v-model="form.is_active" id="skill-active" class="w-4 h-4" />
              <label for="skill-active" class="text-sm text-gray-700 cursor-pointer">Активен (виден пользователям)</label>
            </div>
            <div class="flex items-center gap-2">
              <input type="checkbox" v-model="form.is_maintenance" id="skill-maintenance" class="w-4 h-4 accent-orange-500" />
              <label for="skill-maintenance" class="text-sm text-orange-600 font-medium cursor-pointer">🔧 В ремонте (отображается, но помечен)</label>
            </div>
            <div>
              <label class="label">Порядок сортировки</label>
              <input v-model.number="form.sort_order" type="number" class="input text-sm w-24" />
            </div>
          </div>
          <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-2 shrink-0">
            <button class="btn-secondary text-sm" @click="showModal = false">Отмена</button>
            <button class="btn-primary text-sm" :disabled="saving" @click="save">
              {{ saving ? 'Сохраняю...' : (editingSkill?.id ? 'Сохранить' : 'Создать') }}
            </button>
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
const skills = ref([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)
const editingSkill = ref(null)

const DEFAULTS = {
  name: '', slug: '', description: '', content: '',
  icon: '✨', category: '', is_active: true, is_maintenance: false, sort_order: 0,
}
const form = ref({ ...DEFAULTS })

onMounted(load)

async function load() {
  loading.value = true
  try {
    const res = await adminApi.getSkills()
    skills.value = res.data
  } catch {
    toast.error('Ошибка загрузки скиллов')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingSkill.value = {}
  form.value = { ...DEFAULTS }
  showModal.value = true
}

function openEdit(skill) {
  editingSkill.value = skill
  form.value = {
    name: skill.name,
    slug: skill.slug,
    description: skill.description || '',
    content: skill.content || '',
    icon: skill.icon || '✨',
    category: skill.category || '',
    is_active: skill.is_active,
    is_maintenance: skill.is_maintenance ?? false,
    sort_order: skill.sort_order,
  }
  showModal.value = true
}

async function save() {
  if (!form.value.name || !form.value.slug) {
    toast.error('Заполните название и slug')
    return
  }
  saving.value = true
  try {
    if (editingSkill.value?.id) {
      const res = await adminApi.updateSkill(editingSkill.value.id, form.value)
      const idx = skills.value.findIndex(s => s.id === editingSkill.value.id)
      if (idx !== -1) skills.value[idx] = res.data
      toast.success('Скилл сохранён')
    } else {
      const res = await adminApi.createSkill(form.value)
      skills.value.push(res.data)
      toast.success('Скилл создан')
    }
    showModal.value = false
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  } finally {
    saving.value = false
  }
}

async function deleteSkill(skill) {
  if (!confirm(`Удалить скилл «${skill.name}»?`)) return
  try {
    await adminApi.deleteSkill(skill.id)
    skills.value = skills.value.filter(s => s.id !== skill.id)
    toast.success('Скилл удалён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка')
  }
}
</script>
