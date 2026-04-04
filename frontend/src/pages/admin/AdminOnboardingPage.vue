<template>
  <div class="p-8 max-w-3xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Онбординг</h1>

    <div v-if="loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <template v-else>
      <!-- Глобальные настройки -->
      <div class="card p-6 mb-6">
        <h2 class="font-semibold text-gray-700 mb-4">Общие настройки</h2>
        <div class="space-y-4">
          <div class="flex items-center gap-3">
            <input type="checkbox" id="enabled" v-model="config.enabled" class="w-4 h-4" />
            <label for="enabled" class="text-sm text-gray-700">Показывать онбординг новым пользователям</label>
          </div>
          <div>
            <label class="label">Ссылка на видео (YouTube / Vimeo / прямая)</label>
            <input v-model="config.video_url" class="input" placeholder="https://youtube.com/watch?v=..." />
          </div>
          <div>
            <label class="label">Ссылка поддержки</label>
            <input v-model="config.support_url" class="input" placeholder="https://t.me/ascnai_nocode" />
          </div>
        </div>
      </div>

      <!-- Шаги -->
      <div class="card p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-semibold text-gray-700">Шаги обучения ({{ config.steps.length }})</h2>
          <button class="btn-primary text-sm" @click="addStep">+ Добавить шаг</button>
        </div>

        <div class="space-y-3">
          <div
            v-for="(step, idx) in config.steps"
            :key="step.id"
            class="border border-gray-100 rounded-xl overflow-hidden"
          >
            <!-- Шапка шага -->
            <div
              class="flex items-center gap-3 px-4 py-3 bg-gray-50 cursor-pointer select-none"
              @click="toggleStep(idx)"
            >
              <span class="text-xs font-medium text-gray-400 w-5 text-center">{{ idx + 1 }}</span>
              <span class="flex-1 text-sm font-medium text-gray-700 truncate">{{ step.title || 'Без названия' }}</span>
              <div class="flex gap-1">
                <button
                  class="text-xs text-gray-400 hover:text-gray-600 px-1"
                  :disabled="idx === 0"
                  @click.stop="moveStep(idx, -1)"
                >↑</button>
                <button
                  class="text-xs text-gray-400 hover:text-gray-600 px-1"
                  :disabled="idx === config.steps.length - 1"
                  @click.stop="moveStep(idx, 1)"
                >↓</button>
                <button class="text-xs text-red-400 hover:text-red-600 px-1" @click.stop="removeStep(idx)">✕</button>
              </div>
              <span class="text-gray-400 text-xs">{{ openSteps.has(idx) ? '▲' : '▼' }}</span>
            </div>

            <!-- Тело шага -->
            <div v-if="openSteps.has(idx)" class="px-4 py-4 space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="label">Заголовок</label>
                  <input v-model="step.title" class="input" placeholder="Мой офис" />
                </div>
                <div>
                  <label class="label">CSS-селектор элемента</label>
                  <input v-model="step.element" class="input" placeholder="#nav-office" />
                  <p class="text-xs text-gray-400 mt-1">Оставьте пустым — будет центрированный попап</p>
                </div>
              </div>
              <div>
                <label class="label">Описание (поддерживает HTML)</label>
                <textarea v-model="step.description" class="input min-h-[80px]" placeholder="Текст подсказки..."></textarea>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="label">Маршрут (переход перед шагом)</label>
                  <input v-model="step.route" class="input" placeholder="/cabinet/office" />
                </div>
                <div>
                  <label class="label">Сторона попапа</label>
                  <select v-model="step.side" class="input">
                    <option value="over">Центр (over)</option>
                    <option value="top">Сверху</option>
                    <option value="bottom">Снизу</option>
                    <option value="left">Слева</option>
                    <option value="right">Справа</option>
                  </select>
                </div>
              </div>
              <div>
                <label class="label">URL картинки (необязательно)</label>
                <input v-model="step.image_url" class="input" placeholder="https://..." />
                <img v-if="step.image_url" :src="step.image_url" class="mt-2 rounded-lg max-h-32 object-cover" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Кнопки -->
      <div class="flex gap-3">
        <button class="btn-primary" :disabled="saving" @click="save">
          {{ saving ? 'Сохраняю...' : 'Сохранить' }}
        </button>
        <button class="btn-secondary" @click="resetToDefault">Сбросить к дефолту</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { onboardingApi } from '@/api/onboarding'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const loading = ref(true)
const saving = ref(false)
const openSteps = reactive(new Set())

const config = ref({
  enabled: true,
  video_url: '',
  support_url: 'https://t.me/ascnai_nocode',
  steps: [],
})

onMounted(async () => {
  try {
    const res = await onboardingApi.adminGetConfig()
    config.value = res.data
  } finally {
    loading.value = false
  }
})

function toggleStep(idx) {
  if (openSteps.has(idx)) openSteps.delete(idx)
  else openSteps.add(idx)
}

function addStep() {
  const newStep = {
    id: 'step_' + Date.now(),
    element: '',
    route: '',
    title: '',
    description: '',
    image_url: '',
    side: 'bottom',
  }
  config.value.steps.push(newStep)
  openSteps.add(config.value.steps.length - 1)
}

function removeStep(idx) {
  config.value.steps.splice(idx, 1)
  openSteps.delete(idx)
}

function moveStep(idx, dir) {
  const arr = config.value.steps
  const newIdx = idx + dir
  if (newIdx < 0 || newIdx >= arr.length) return
  ;[arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]]
}

async function save() {
  saving.value = true
  try {
    await onboardingApi.adminSaveConfig(config.value)
    toast.success('Онбординг сохранён')
  } catch {
    toast.error('Ошибка сохранения')
  } finally {
    saving.value = false
  }
}

async function resetToDefault() {
  if (!confirm('Сбросить все шаги к дефолтным настройкам?')) return
  try {
    // Загружаем дефолт с сервера (он отдаёт дефолт если нет записи в БД)
    await onboardingApi.adminSaveConfig({ ...config.value, steps: [] })
    const res = await onboardingApi.adminGetConfig()
    config.value = res.data
    openSteps.clear()
    toast.success('Сброшено к дефолту')
  } catch {
    toast.error('Ошибка')
  }
}
</script>
