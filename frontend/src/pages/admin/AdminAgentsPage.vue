<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Шаблонные агенты</h1>
      <button class="btn-primary" @click="openCreate">+ Создать</button>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Список шаблонов -->
      <div class="lg:col-span-1 space-y-2">
        <div
          v-for="t in templates"
          :key="t.id"
          class="card p-4 cursor-pointer hover:shadow-md transition-shadow"
          :class="selected?.id === t.id ? 'border-primary-400 bg-primary-50/50' : ''"
          @click="selectTemplate(t)"
        >
          <div class="flex items-center justify-between">
            <span class="font-medium text-sm text-gray-900">{{ t.name }}</span>
            <span :class="t.is_active ? 'badge-active' : 'badge-inactive'">
              {{ t.is_active ? 'Активен' : 'Откл.' }}
            </span>
          </div>
          <p class="text-xs text-gray-400 mt-1 line-clamp-1">{{ t.description || '—' }}</p>
        </div>
      </div>

      <!-- Форма редактирования -->
      <div v-if="selected" class="lg:col-span-2 card p-0 overflow-hidden">
        <!-- Вкладки -->
        <div class="flex border-b border-gray-100">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="px-5 py-3 text-sm font-medium transition-colors"
            :class="activeTab === tab.key ? 'text-primary-600 border-b-2 border-primary-500' : 'text-gray-500 hover:text-gray-700'"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
          <div class="ml-auto flex items-center px-4 gap-2">
            <button class="btn-danger text-xs" @click="deleteTemplate">Удалить</button>
            <button class="btn-primary text-xs" @click="saveTemplate" :disabled="saving">
              {{ saving ? 'Сохраняю...' : 'Сохранить' }}
            </button>
          </div>
        </div>

        <div class="p-6">
          <!-- Вкладка: Основное -->
          <div v-if="activeTab === 'basic'" class="space-y-4">
            <div>
              <label class="label">Название</label>
              <input v-model="form.name" class="input" />
            </div>
            <div>
              <label class="label">Описание</label>
              <textarea v-model="form.description" class="input resize-none h-20"></textarea>
            </div>
            <div>
              <label class="label">Языковая модель (OpenRouter)</label>
              <select v-model="form.llm_model" class="input text-sm">
                <option value="">— Выберите модель —</option>
                <optgroup label="OpenAI">
                  <option value="openai/gpt-4o">GPT-4o</option>
                  <option value="openai/gpt-4o-mini">GPT-4o Mini</option>
                  <option value="openai/gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="openai/o1-mini">o1-mini</option>
                </optgroup>
                <optgroup label="Anthropic">
                  <option value="anthropic/claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                  <option value="anthropic/claude-3-5-haiku">Claude 3.5 Haiku</option>
                  <option value="anthropic/claude-3-opus">Claude 3 Opus</option>
                </optgroup>
                <optgroup label="Google">
                  <option value="google/gemini-2.0-flash-001">Gemini 2.0 Flash</option>
                  <option value="google/gemini-pro-1.5">Gemini 1.5 Pro</option>
                </optgroup>
                <optgroup label="Meta / Open Source">
                  <option value="meta-llama/llama-3.3-70b-instruct">Llama 3.3 70B</option>
                  <option value="mistralai/mistral-large">Mistral Large</option>
                  <option value="deepseek/deepseek-chat">DeepSeek Chat</option>
                </optgroup>
              </select>
            </div>
            <div>
              <label class="label">API-ключ OpenRouter</label>
              <input v-model="form.llm_token" class="input font-mono text-sm" type="password" placeholder="sk-or-v1-..." autocomplete="off" />
            </div>
            <div class="flex items-center gap-3">
              <input type="checkbox" v-model="form.is_active" class="w-4 h-4 rounded" />
              <label class="text-sm text-gray-700">Активен (виден пользователям)</label>
            </div>

            <!-- Подсказки -->
            <div>
              <label class="label">Быстрые подсказки <span class="text-xs font-normal text-gray-400">(до 3 кнопок над полем ввода)</span></label>
              <div class="space-y-2">
                <input
                  v-for="(_, i) in 3"
                  :key="i"
                  v-model="form.prompt_suggestions[i]"
                  class="input text-sm"
                  :placeholder="`Подсказка ${i + 1}, напр. «Что ты умеешь?»`"
                />
              </div>
            </div>
          </div>

          <!-- Вкладка: Промпт и скиллы -->
          <div v-else-if="activeTab === 'prompt'" class="space-y-4">
            <div>
              <label class="label">Системный промпт</label>
              <textarea v-model="form.prompt" class="input resize-none h-40 font-mono text-sm"></textarea>
            </div>
            <div>
              <label class="label">Скиллы / Знания</label>
              <textarea v-model="form.skills" class="input resize-none h-24 font-mono text-sm"></textarea>
            </div>
          </div>

          <!-- Вкладка: Скиллы из каталога -->
          <div v-else-if="activeTab === 'skills_catalog'" class="space-y-3">
            <p class="text-xs text-gray-400">Скиллы из каталога, которые будут предустановлены агенту при создании из шаблона. Также можно управлять видимостью скилла для пользователей.</p>
            <div v-if="!allSkills.length" class="text-center py-8 text-gray-400 text-sm">Скиллов пока нет. Создайте их в разделе «Скиллы».</div>
            <div
              v-for="skill in allSkills"
              :key="skill.id"
              class="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:border-gray-200"
              :class="!skill.is_active ? 'opacity-60' : ''"
            >
              <!-- Чекбокс: предустановить в шаблон -->
              <input type="checkbox" :value="skill.id" v-model="form.skill_ids" class="w-4 h-4 rounded shrink-0" />
              <span class="text-xl shrink-0">{{ skill.icon }}</span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="font-medium text-sm text-gray-900">{{ skill.name }}</span>
                  <span v-if="skill.category" class="text-xs px-1.5 py-0.5 bg-purple-50 text-purple-600 rounded-full border border-purple-100">{{ skill.category }}</span>
                </div>
                <div v-if="skill.description" class="text-xs text-gray-400 truncate">{{ skill.description }}</div>
              </div>
              <!-- Тоггл: виден пользователям -->
              <div class="flex items-center gap-1.5 shrink-0">
                <span class="text-xs text-gray-400">{{ skill.is_active ? 'Виден' : 'Скрыт' }}</span>
                <button
                  class="relative w-9 h-5 rounded-full transition-colors shrink-0"
                  :class="skill.is_active ? 'bg-green-400' : 'bg-gray-200'"
                  @click="toggleSkillVisibility(skill)"
                >
                  <span
                    class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"
                    :class="skill.is_active ? 'translate-x-4' : 'translate-x-0.5'"
                  ></span>
                </button>
              </div>
            </div>
          </div>

          <!-- Вкладка: Инструменты -->
          <div v-else-if="activeTab === 'tools'" class="space-y-3">
            <div
              v-for="tool in allTools"
              :key="tool.id"
              class="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:border-gray-200"
            >
              <input type="checkbox" :value="tool.id" v-model="form.tool_ids" class="w-4 h-4 rounded shrink-0" />
              <div class="flex-1 min-w-0">
                <div class="font-medium text-sm text-gray-900">{{ tool.name }}</div>
                <div class="text-xs text-gray-400 line-clamp-1">{{ tool.description }}</div>
              </div>
              <div class="text-xs text-gray-400 shrink-0">⚡{{ tool.energy_cost }}</div>
            </div>
          </div>

          <!-- Вкладка: Энергия -->
          <div v-else-if="activeTab === 'energy'" class="space-y-4">
            <div>
              <label class="label">Энергия за вызов чата</label>
              <input v-model.number="form.energy_per_chat" type="number" min="0" class="input w-40" />
            </div>
            <div class="p-4 bg-gray-50 rounded-lg text-sm text-gray-600">
              <div class="font-medium mb-2">Итого за один вызов:</div>
              <div>Чат: ⚡{{ form.energy_per_chat }}</div>
              <div v-for="tid in form.tool_ids" :key="tid">
                {{ getToolName(tid) }}: ⚡{{ getToolCost(tid) }}
              </div>
              <div class="border-t border-gray-200 mt-2 pt-2 font-semibold">
                Итого: ⚡{{ totalEnergy }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="lg:col-span-2 flex items-center justify-center text-gray-400 text-sm">
        Выберите шаблон для редактирования
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const templates = ref([])
const allTools = ref([])
const loading = ref(true)
const saving = ref(false)
const selected = ref(null)
const activeTab = ref('basic')

const tabs = [
  { key: 'basic', label: 'Основное' },
  { key: 'prompt', label: 'Промпт и скиллы' },
  { key: 'skills_catalog', label: 'Скиллы' },
  { key: 'tools', label: 'Инструменты' },
  { key: 'energy', label: 'Энергия' },
]

const form = ref({
  name: '', description: '', llm_url: '', llm_model: '', llm_token: '', prompt: '', skills: '',
  is_active: true, energy_per_chat: 5, tool_ids: [], skill_ids: [], prompt_suggestions: ['', '', ''],
})

const totalEnergy = computed(() => {
  const toolsCost = form.value.tool_ids.reduce((sum, tid) => sum + getToolCost(tid), 0)
  return form.value.energy_per_chat + toolsCost
})

const allSkills = ref([])

onMounted(async () => {
  const [tRes, toolsRes, skillsRes] = await Promise.allSettled([
    adminApi.getTemplates(),
    adminApi.getTools(),
    adminApi.getSkills(),
  ])
  if (tRes.status === 'fulfilled') templates.value = tRes.value.data
  if (toolsRes.status === 'fulfilled') allTools.value = toolsRes.value.data
  if (skillsRes.status === 'fulfilled') allSkills.value = skillsRes.value.data
  loading.value = false
})

function selectTemplate(t) {
  selected.value = t
  activeTab.value = 'basic'
  const s = t.prompt_suggestions ?? []
  form.value = {
    name: t.name,
    description: t.description,
    llm_url: t.llm_url,
    llm_model: t.llm_model ?? '',
    llm_token: t.llm_token ?? '',
    prompt: t.prompt,
    skills: t.skills,
    is_active: t.is_active,
    energy_per_chat: t.energy_per_chat,
    tool_ids: t.tools?.map((tool) => tool.id) ?? [],
    skill_ids: t.skill_ids ?? [],
    prompt_suggestions: [s[0] ?? '', s[1] ?? '', s[2] ?? ''],
  }
}

function openCreate() {
  selected.value = { id: null }
  activeTab.value = 'basic'
  form.value = { name: '', description: '', llm_url: '', llm_model: '', llm_token: '', prompt: '', skills: '', is_active: true, energy_per_chat: 5, tool_ids: [], skill_ids: [], prompt_suggestions: ['', '', ''] }
}

async function saveTemplate() {
  saving.value = true
  try {
    const payload = { ...form.value, prompt_suggestions: form.value.prompt_suggestions.filter(s => s.trim()) }
    if (selected.value.id) {
      const res = await adminApi.updateTemplate(selected.value.id, payload)
      selected.value = res.data
      const idx = templates.value.findIndex((t) => t.id === selected.value.id)
      if (idx !== -1) templates.value[idx] = res.data
    } else {
      const res = await adminApi.createTemplate(payload)
      templates.value.push(res.data)
      selected.value = res.data
    }
    toast.success('Сохранено')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка сохранения')
  } finally {
    saving.value = false
  }
}

async function deleteTemplate() {
  if (!selected.value.id) return
  if (!confirm('Удалить шаблон?')) return
  try {
    await adminApi.deleteTemplate(selected.value.id)
    templates.value = templates.value.filter((t) => t.id !== selected.value.id)
    selected.value = null
    toast.success('Шаблон удалён')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка удаления')
  }
}

function getToolName(id) {
  return allTools.value.find((t) => t.id === id)?.name ?? id
}
function getToolCost(id) {
  return allTools.value.find((t) => t.id === id)?.energy_cost ?? 0
}

async function toggleSkillVisibility(skill) {
  try {
    const res = await adminApi.updateSkill(skill.id, { is_active: !skill.is_active })
    const idx = allSkills.value.findIndex(s => s.id === skill.id)
    if (idx !== -1) allSkills.value[idx] = res.data
  } catch {
    // тихо
  }
}
</script>
