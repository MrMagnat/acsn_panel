<template>
  <div class="flex flex-col h-screen">
    <!-- Шапка -->
    <div class="flex items-center gap-4 px-6 py-4 border-b border-gray-100 bg-white shrink-0">
      <button class="text-gray-400 hover:text-gray-600 text-lg" @click="router.push('/cabinet/knowledge-base')">←</button>
      <div v-if="!renamingKb" class="flex items-center gap-2">
        <h1 class="text-lg font-semibold text-gray-900">{{ kb?.name }}</h1>
        <button class="text-xs text-gray-400 hover:text-gray-600" @click="startRenameKb">✏️</button>
      </div>
      <form v-else @submit.prevent="saveRenameKb" class="flex items-center gap-2">
        <input v-model="kbNewName" class="input text-sm" autofocus @blur="saveRenameKb" />
      </form>

      <div class="ml-auto flex items-center gap-2">
        <span class="text-xs text-gray-400">{{ kb?.records?.length ?? 0 }} строк · {{ kb?.fields?.length ?? 0 }} колонок</span>
        <button class="btn-secondary text-xs" @click="openWebhook">🔗 Вебхук</button>
        <label class="btn-secondary text-xs cursor-pointer">
          📥 Импорт CSV
          <input type="file" accept=".csv" class="hidden" @change="importCsv" />
        </label>
        <button class="btn-secondary text-xs" @click="exportCsv">📤 Экспорт CSV</button>
        <button class="btn-primary text-xs" @click="addRow">+ Строка</button>
      </div>
    </div>

    <!-- Таблица -->
    <div v-if="loading" class="flex-1 flex items-center justify-center text-gray-400">Загрузка...</div>

    <div v-else class="flex-1 overflow-auto">
      <table class="w-full caption-bottom text-sm" style="min-width: max-content">
        <thead class="sticky top-0 z-10 bg-white [&_tr]:border-b [&_tr]:border-gray-200">
          <tr>
            <th class="h-11 w-10 px-3 text-center align-middle text-xs font-normal text-gray-400 border-r border-gray-200">#</th>
            <th
              v-for="field in kb.fields"
              :key="field.id"
              class="h-11 px-3 text-left align-middle text-xs font-medium text-gray-500 min-w-[140px] border-r border-gray-200 group"
            >
              <div class="flex items-center gap-1">
                <span v-if="!renamingField || renamingField !== field.id" class="flex-1 truncate">{{ field.name }}</span>
                <input
                  v-else
                  v-model="fieldNewName"
                  class="flex-1 text-xs border border-primary-300 rounded px-1 py-0.5 outline-none"
                  autofocus
                  @blur="saveRenameField(field)"
                  @keydown.enter="saveRenameField(field)"
                  @keydown.escape="renamingField = null"
                />
                <button
                  class="opacity-0 group-hover:opacity-100 text-xs text-gray-400 hover:text-primary-500 shrink-0"
                  @click="startRenameField(field)"
                >✏️</button>
                <button
                  class="opacity-0 group-hover:opacity-100 text-xs text-gray-400 hover:text-red-500 shrink-0"
                  @click="deleteField(field)"
                >✕</button>
              </div>
            </th>
            <th class="h-11 px-3 w-10 align-middle">
              <button class="text-gray-400 hover:text-primary-600 font-bold text-lg leading-none" @click="showAddField = true">+</button>
            </th>
          </tr>
        </thead>
        <tbody class="[&_tr:last-child]:border-0">
          <tr
            v-for="(record, rowIdx) in kb.records"
            :key="record.id"
            class="border-b border-gray-100 transition-colors hover:bg-gray-50/60 group/row"
          >
            <td class="px-3 py-2 align-middle text-xs text-gray-400 text-center border-r border-gray-100">
              <div class="flex items-center justify-center gap-1">
                <span>{{ rowIdx + 1 }}</span>
                <button
                  class="opacity-0 group-hover/row:opacity-100 text-red-400 hover:text-red-600 text-xs"
                  @click="deleteRecord(record)"
                >✕</button>
              </div>
            </td>
            <td
              v-for="field in kb.fields"
              :key="field.id"
              class="p-0 align-middle border-r border-gray-100 min-w-[140px] max-w-[300px]"
              @click="startEdit(record, field.name)"
            >
              <input
                v-if="editing?.recordId === record.id && editing?.fieldName === field.name"
                v-model="editValue"
                class="w-full px-3 py-2 outline-none bg-primary-50 ring-1 ring-inset ring-primary-300 text-sm"
                autofocus
                @blur="saveEdit"
                @keydown.enter="saveEdit"
                @keydown.escape="editing = null"
              />
              <div v-else class="px-3 py-2 text-gray-700 truncate cursor-text min-h-[36px]">
                {{ record.data[field.name] ?? '' }}
              </div>
            </td>
            <td class="border-r-0"></td>
          </tr>

          <tr>
            <td class="px-3 py-2" colspan="999">
              <button class="text-xs text-gray-400 hover:text-primary-600" @click="addRow">+ Добавить строку</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Модал вебхука -->
    <div v-if="showWebhook" class="fixed inset-0 bg-black/40 z-40 flex items-center justify-center p-4" @click.self="showWebhook = false">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold text-gray-900">🔗 Вебхук для базы знаний</h2>
          <button class="text-gray-400 hover:text-gray-600" @click="showWebhook = false">✕</button>
        </div>

        <div class="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3 text-sm text-gray-700">
          <p>
            Отправьте <strong>POST-запрос</strong> на этот URL — и строка появится в базе знаний.
          </p>
          <p>
            <strong>Токен</strong> — уникальный секретный ключ этой базы, вшитый в ссылку.
            Он защищает от несанкционированного доступа — никому не передавайте ссылку целиком.
          </p>
        </div>

        <div v-if="webhookLoading" class="text-sm text-gray-400 text-center py-2">Генерируем ссылку...</div>
        <div v-else-if="webhookUrl" class="space-y-3">
          <div>
            <label class="text-xs font-medium text-gray-500 mb-1 block">URL вебхука (POST-запрос)</label>
            <div class="flex gap-2">
              <input
                :value="webhookUrl"
                readonly
                class="input text-xs font-mono flex-1 bg-gray-50"
                @click="$event.target.select()"
              />
              <button
                class="btn-secondary text-xs shrink-0"
                @click="copyUrl"
              >{{ copied ? '✓ Скопировано' : 'Копировать' }}</button>
            </div>
          </div>

          <div class="p-3 bg-blue-50 rounded-lg border border-blue-100 text-xs text-blue-700 space-y-1.5">
            <p class="font-medium">Пример запроса:</p>
            <pre class="whitespace-pre-wrap font-mono">POST {{ webhookUrl }}
Content-Type: application/json

{
  "{{ kb?.fields?.[0]?.name || 'поле' }}": "значение",
  "{{ kb?.fields?.[1]?.name || 'другое_поле' }}": "значение"
}</pre>
          </div>
        </div>

        <button class="w-full btn-secondary text-sm" @click="showWebhook = false">Закрыть</button>
      </div>
    </div>

    <!-- Модал добавления колонки -->
    <div v-if="showAddField" class="fixed inset-0 bg-black/40 z-40 flex items-center justify-center p-4" @click.self="showAddField = false">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
        <h2 class="font-semibold mb-4">Новая колонка</h2>
        <form @submit.prevent="addField">
          <label class="label">Название</label>
          <input v-model="newFieldName" class="input mb-3" placeholder="Телефон" autofocus required />
          <label class="label">Тип данных</label>
          <select v-model="newFieldType" class="input mb-4">
            <option value="text">Текст</option>
            <option value="number">Число</option>
            <option value="email">Email</option>
            <option value="phone">Телефон</option>
            <option value="url">Ссылка</option>
          </select>
          <div class="flex gap-2">
            <button type="button" class="btn-secondary flex-1" @click="showAddField = false">Отмена</button>
            <button type="submit" class="btn-primary flex-1">Добавить</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { kbApi } from '@/api/knowledge-base'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const kb = ref(null)
const loading = ref(true)

// Редактирование ячейки
const editing = ref(null)
const editValue = ref('')

// Переименование базы
const renamingKb = ref(false)
const kbNewName = ref('')

// Переименование поля
const renamingField = ref(null)
const fieldNewName = ref('')

// Добавление поля
const showAddField = ref(false)
const newFieldName = ref('')
const newFieldType = ref('text')

// Вебхук
const showWebhook = ref(false)
const webhookUrl = ref('')
const webhookLoading = ref(false)
const copied = ref(false)

onMounted(load)

async function openWebhook() {
  showWebhook.value = true
  if (webhookUrl.value) return
  webhookLoading.value = true
  try {
    const res = await kbApi.webhookToken(kb.value.id)
    const base = window.location.origin + '/api'
    webhookUrl.value = `${base}/webhooks/kb/${kb.value.id}?token=${res.data.token}`
  } catch {
    toast.error('Не удалось получить токен')
  } finally {
    webhookLoading.value = false
  }
}

async function copyUrl() {
  try {
    await navigator.clipboard.writeText(webhookUrl.value)
  } catch {
    // fallback для http
    const el = document.createElement('textarea')
    el.value = webhookUrl.value
    el.style.position = 'fixed'
    el.style.opacity = '0'
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

async function load() {
  loading.value = true
  try {
    const res = await kbApi.get(route.params.id)
    kb.value = res.data
  } finally {
    loading.value = false
  }
}

// ─── Ячейки ───────────────────────────────────────────────────────────────────

function startEdit(record, fieldName) {
  editing.value = { recordId: record.id, fieldName }
  editValue.value = record.data[fieldName] ?? ''
}

async function saveEdit() {
  if (!editing.value) return
  const { recordId, fieldName } = editing.value
  const record = kb.value.records.find((r) => r.id === recordId)
  if (record && record.data[fieldName] !== editValue.value) {
    record.data[fieldName] = editValue.value
    await kbApi.updateRecord(kb.value.id, recordId, { [fieldName]: editValue.value })
  }
  editing.value = null
}

// ─── Строки ───────────────────────────────────────────────────────────────────

async function addRow() {
  try {
    const res = await kbApi.addRecord(kb.value.id)
    kb.value.records.push(res.data)
  } catch {
    toast.error('Ошибка добавления строки')
  }
}

async function deleteRecord(record) {
  if (!confirm('Удалить строку?')) return
  try {
    await kbApi.deleteRecord(kb.value.id, record.id)
    kb.value.records = kb.value.records.filter((r) => r.id !== record.id)
  } catch {
    toast.error('Ошибка удаления')
  }
}

// ─── Колонки ──────────────────────────────────────────────────────────────────

async function addField() {
  if (!newFieldName.value.trim()) return
  try {
    const res = await kbApi.addField(kb.value.id, newFieldName.value.trim(), newFieldType.value)
    kb.value.fields.push(res.data)
    showAddField.value = false
    newFieldName.value = ''
    newFieldType.value = 'text'
  } catch {
    toast.error('Ошибка добавления колонки')
  }
}

function startRenameField(field) {
  renamingField.value = field.id
  fieldNewName.value = field.name
}

async function saveRenameField(field) {
  if (!renamingField.value) return
  const newName = fieldNewName.value.trim()
  if (newName && newName !== field.name) {
    // Обновляем ключи в существующих записях (локально)
    kb.value.records.forEach((r) => {
      if (field.name in r.data) {
        r.data[newName] = r.data[field.name]
        delete r.data[field.name]
      }
    })
    await kbApi.updateField(kb.value.id, field.id, { name: newName })
    field.name = newName
  }
  renamingField.value = null
}

async function deleteField(field) {
  if (!confirm(`Удалить колонку «${field.name}»? Данные в этой колонке будут потеряны.`)) return
  try {
    await kbApi.deleteField(kb.value.id, field.id)
    kb.value.fields = kb.value.fields.filter((f) => f.id !== field.id)
    kb.value.records.forEach((r) => delete r.data[field.name])
  } catch {
    toast.error('Ошибка удаления колонки')
  }
}

// ─── Переименование базы ──────────────────────────────────────────────────────

function startRenameKb() {
  renamingKb.value = true
  kbNewName.value = kb.value.name
}

async function saveRenameKb() {
  const newName = kbNewName.value.trim()
  if (newName && newName !== kb.value.name) {
    await kbApi.rename(kb.value.id, newName)
    kb.value.name = newName
  }
  renamingKb.value = false
}

// ─── Экспорт CSV ─────────────────────────────────────────────────────────────

async function exportCsv() {
  try {
    const res = await kbApi.exportCsv(kb.value.id)
    const url = URL.createObjectURL(new Blob([res.data], { type: 'text/csv' }))
    const a = document.createElement('a')
    a.href = url
    a.download = (kb.value.name || 'export') + '.csv'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    toast.error('Ошибка экспорта')
  }
}

// ─── Импорт CSV ───────────────────────────────────────────────────────────────

async function importCsv(e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    const res = await kbApi.importCsv(kb.value.id, file)
    toast.success(`Импортировано ${res.data.imported} строк`)
    await load()
  } catch {
    toast.error('Ошибка импорта CSV')
  }
  e.target.value = ''
}
</script>
