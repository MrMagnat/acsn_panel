<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Инструменты</h1>
      <button class="btn-primary" @click="openCreate">+ Создать</button>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Список -->
      <div class="lg:col-span-1 space-y-2">
        <div
          v-for="tool in tools"
          :key="tool.id"
          class="card p-4 cursor-pointer hover:shadow-md transition-shadow"
          :class="selected?.id === tool.id ? 'border-primary-400 bg-primary-50/50' : ''"
          @click="selectTool(tool)"
        >
          <div class="flex items-center justify-between">
            <span class="font-medium text-sm text-gray-900">{{ tool.name }}</span>
            <span :class="tool.is_active ? 'badge-active' : 'badge-inactive'">
              {{ tool.is_active ? 'Активен' : 'Откл.' }}
            </span>
          </div>
          <p class="text-xs text-gray-400 mt-1 line-clamp-1">{{ tool.description || '—' }}</p>
          <p class="text-xs text-gray-400 mt-1">⚡ {{ tool.energy_cost }} · {{ tool.fields?.length ?? 0 }} полей</p>
        </div>
      </div>

      <!-- Форма редактирования -->
      <div v-if="selected" class="lg:col-span-2 card p-6 space-y-5">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <h2 class="font-semibold">{{ selected.id ? 'Редактировать инструмент' : 'Новый инструмент' }}</h2>
          <div class="flex gap-2">
            <button v-if="selected.id" class="btn-danger text-xs" @click="deleteTool">Удалить</button>
            <button class="btn-primary text-xs" @click="saveTool" :disabled="saving">
              {{ saving ? 'Сохраняю...' : 'Сохранить' }}
            </button>
          </div>
        </div>

        <!-- Основные поля -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Название</label>
            <input v-model="form.name" class="input" />
          </div>
          <div>
            <label class="label">Стоимость энергии</label>
            <input v-model.number="form.energy_cost" type="number" min="0" class="input" />
          </div>
        </div>
        <div>
          <label class="label">Описание</label>
          <textarea v-model="form.description" class="input resize-none h-16" placeholder="Что делает инструмент..."></textarea>
        </div>
        <div>
          <label class="label">
            Когда использовать
            <span class="text-xs font-normal text-gray-400 ml-1">(подсказка для ИИ)</span>
          </label>
          <textarea
            v-model="form.trigger_hint"
            class="input resize-none h-16"
            placeholder="Используй когда пользователь просит разослать сообщение, уведомить подписчиков, сделать рассылку..."
          ></textarea>
          <p class="text-xs text-gray-400 mt-1">Объясните ИИ-агенту в каких случаях вызывать этот инструмент</p>
        </div>
        <div>
          <label class="label">Webhook URL</label>
          <input v-model="form.webhook_url" class="input font-mono text-sm" placeholder="https://workflow-engine.example.com/hook/..." />
        </div>
        <div class="flex items-center gap-3">
          <input type="checkbox" v-model="form.is_active" class="w-4 h-4 rounded" />
          <label class="text-sm text-gray-700">Активен (доступен пользователям)</label>
        </div>

        <!-- Поля вебхука -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <label class="label mb-0">Поля для заполнения пользователем</label>
            <button class="text-xs text-primary-600 hover:underline" @click="addField">+ Добавить поле</button>
          </div>
          <div class="space-y-3">
            <div
              v-for="(field, idx) in form.fields"
              :key="idx"
              class="p-3 rounded-lg bg-gray-50 border border-gray-100 space-y-2"
            >
              <div class="grid grid-cols-3 gap-2">
                <div>
                  <label class="text-xs text-gray-500">Название поля</label>
                  <input v-model="field.field_name" class="input text-xs mt-0.5" placeholder="api_key" />
                </div>
                <div>
                  <label class="text-xs text-gray-500">Тип</label>
                  <select v-model="field.field_type" class="input text-xs mt-0.5">
                    <option value="text">text — строка</option>
                    <option value="url">url — ссылка</option>
                    <option value="number">number — число</option>
                    <option value="json">json — объект JSON</option>
                    <option value="select">select — выбор из списка</option>
                    <option value="array">array — массив</option>
                    <option value="base">base — база знаний</option>
                  </select>
                </div>
                <div class="flex flex-col">
                  <label class="text-xs text-gray-500">Обязательное</label>
                  <div class="flex items-center gap-2 mt-2">
                    <input type="checkbox" v-model="field.required" class="w-4 h-4" />
                    <button class="text-red-400 hover:text-red-600 text-xs ml-auto" @click="removeField(idx)">Удалить</button>
                  </div>
                </div>
              </div>
              <div>
                <label class="text-xs text-gray-500">Подсказка (hint)</label>
                <input v-model="field.hint" class="input text-xs mt-0.5" placeholder="Введите ваш API ключ..." />
              </div>
              <!-- Варианты для select -->
              <div v-if="field.field_type === 'select'">
                <label class="text-xs text-gray-500">Варианты выбора <span class="text-gray-400">(каждый с новой строки)</span></label>
                <textarea
                  class="input text-xs mt-0.5 resize-none h-20 font-mono"
                  placeholder="Красота&#10;Технологии&#10;Криптовалюта"
                  :value="optionsToText(field.options)"
                  @input="field.options = textToOptions($event.target.value)"
                ></textarea>
              </div>
              <!-- Подсказка для json -->
              <div v-if="field.field_type === 'json'" class="text-xs text-blue-500 bg-blue-50 rounded px-2 py-1">
                Пользователь введёт JSON-объект. В webhook отправится как строка.
              </div>
              <!-- Подсказка для array -->
              <div v-if="field.field_type === 'array'" class="text-xs text-purple-600 bg-purple-50 rounded px-2 py-1">
                Пользователь введёт элементы построчно → в webhook отправится как <code>["элемент1", "элемент2"]</code>
              </div>
              <!-- Подсказка для base -->
              <div v-if="field.field_type === 'base'" class="text-xs text-green-700 bg-green-50 rounded px-2 py-1">
                Пользователь выберет свою базу знаний и колонки при запуске → в webhook отправится как <code>[[val1, val2], [val1, val2]]</code>
              </div>
              <!-- is_runtime toggle -->
              <div class="flex items-center gap-2 pt-1 border-t border-gray-200">
                <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" v-model="field.is_runtime" class="sr-only peer" />
                  <div class="w-8 h-4 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:bg-primary-500 after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:after:translate-x-4"></div>
                </label>
                <span class="text-xs" :class="field.is_runtime ? 'text-primary-600 font-medium' : 'text-gray-400'">
                  {{ field.is_runtime ? '💬 Параметр чата — ИИ может задать через разговор' : 'Только настройки — ИИ не трогает' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="lg:col-span-2 flex items-center justify-center text-gray-400 text-sm">
        Выберите инструмент для редактирования
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const tools = ref([])
const loading = ref(true)
const saving = ref(false)
const selected = ref(null)

const form = ref({
  name: '', description: '', trigger_hint: '', webhook_url: '', is_active: true,
  energy_cost: 10, fields: [],
})

onMounted(async () => {
  const res = await adminApi.getTools()
  tools.value = res.data
  loading.value = false
})

function selectTool(tool) {
  selected.value = tool
  form.value = {
    name: tool.name,
    description: tool.description,
    trigger_hint: tool.trigger_hint ?? '',
    webhook_url: tool.webhook_url,
    is_active: tool.is_active,
    energy_cost: tool.energy_cost,
    fields: tool.fields?.map((f) => ({ ...f })) ?? [],
  }
}

function openCreate() {
  selected.value = { id: null }
  form.value = { name: '', description: '', trigger_hint: '', webhook_url: '', is_active: true, energy_cost: 10, fields: [] }
}

function addField() {
  form.value.fields.push({ field_name: '', hint: '', required: false, field_type: 'text', sort_order: form.value.fields.length, is_runtime: false, options: null })
}

// Конвертация options JSON <-> текст (одна строка = один вариант)
function optionsToText(options) {
  if (!options) return ''
  try { return JSON.parse(options).join('\n') } catch { return options }
}
function textToOptions(text) {
  const lines = text.split('\n').map(s => s.trim()).filter(Boolean)
  return lines.length ? JSON.stringify(lines) : null
}

function removeField(idx) {
  form.value.fields.splice(idx, 1)
}

async function saveTool() {
  saving.value = true
  try {
    if (selected.value.id) {
      const res = await adminApi.updateTool(selected.value.id, form.value)
      selected.value = res.data
      const idx = tools.value.findIndex((t) => t.id === selected.value.id)
      if (idx !== -1) tools.value[idx] = res.data
    } else {
      const res = await adminApi.createTool(form.value)
      tools.value.push(res.data)
      selected.value = res.data
    }
    toast.success('Инструмент сохранён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка сохранения')
  } finally {
    saving.value = false
  }
}

async function deleteTool() {
  if (!confirm('Удалить инструмент?')) return
  try {
    await adminApi.deleteTool(selected.value.id)
    tools.value = tools.value.filter((t) => t.id !== selected.value.id)
    selected.value = null
    toast.success('Инструмент удалён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка удаления')
  }
}
</script>
