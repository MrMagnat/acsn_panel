<template>
  <div class="fixed inset-0 bg-black/40 z-40 flex items-center justify-center p-4" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 sticky top-0 bg-white z-10">
        <h2 class="font-semibold text-gray-900">Редактировать агента</h2>
        <button class="text-gray-400 hover:text-gray-600 text-xl" @click="$emit('close')">✕</button>
      </div>
      <form @submit.prevent="handleSave" class="p-6 space-y-4">
        <div>
          <label class="label">Название</label>
          <input v-model="form.name" class="input" required />
        </div>
        <div>
          <label class="label">Описание</label>
          <textarea v-model="form.description" class="input resize-none h-20"></textarea>
        </div>

        <div>
          <label class="label">Языковая модель</label>
          <select v-model="form.llm_model" class="input text-sm">
            <option value="">— Выберите модель —</option>
            <optgroup label="🆓 Бесплатные">
              <option value="google/gemini-2.0-flash-exp:free">Gemini 2.0 Flash (бесплатно)</option>
              <option value="deepseek/deepseek-r1:free">DeepSeek R1 (бесплатно)</option>
              <option value="deepseek/deepseek-chat-v3-0324:free">DeepSeek V3 (бесплатно)</option>
              <option value="meta-llama/llama-3.3-70b-instruct:free">Llama 3.3 70B (бесплатно)</option>
              <option value="meta-llama/llama-3.1-8b-instruct:free">Llama 3.1 8B (бесплатно)</option>
              <option value="mistralai/mistral-7b-instruct:free">Mistral 7B (бесплатно)</option>
              <option value="qwen/qwen-2.5-72b-instruct:free">Qwen 2.5 72B (бесплатно)</option>
            </optgroup>
            <optgroup label="OpenAI">
              <option value="openai/gpt-4o">GPT-4o</option>
              <option value="openai/gpt-4o-mini">GPT-4o Mini</option>
              <option value="openai/gpt-4.5-preview">GPT-4.5 Preview</option>
              <option value="openai/o3-mini">o3-mini</option>
              <option value="openai/o1">o1</option>
            </optgroup>
            <optgroup label="Anthropic">
              <option value="anthropic/claude-3-7-sonnet">Claude 3.7 Sonnet</option>
              <option value="anthropic/claude-3-5-sonnet">Claude 3.5 Sonnet</option>
              <option value="anthropic/claude-3-5-haiku">Claude 3.5 Haiku</option>
              <option value="anthropic/claude-3-opus">Claude 3 Opus</option>
            </optgroup>
            <optgroup label="Google">
              <option value="google/gemini-2.0-flash-001">Gemini 2.0 Flash</option>
              <option value="google/gemini-2.0-pro-exp-02-05">Gemini 2.0 Pro</option>
              <option value="google/gemini-flash-1.5">Gemini 1.5 Flash</option>
              <option value="google/gemini-pro-1.5">Gemini 1.5 Pro</option>
            </optgroup>
            <optgroup label="DeepSeek">
              <option value="deepseek/deepseek-r1">DeepSeek R1</option>
              <option value="deepseek/deepseek-chat-v3-0324">DeepSeek V3</option>
            </optgroup>
            <optgroup label="Meta / Open Source">
              <option value="meta-llama/llama-3.3-70b-instruct">Llama 3.3 70B</option>
              <option value="mistralai/mistral-large">Mistral Large</option>
              <option value="mistralai/mistral-small-3.1-24b-instruct">Mistral Small 3.1</option>
              <option value="qwen/qwen-2.5-72b-instruct">Qwen 2.5 72B</option>
            </optgroup>
          </select>
          <p class="text-xs text-gray-400 mt-1">
            Модели через <a href="https://openrouter.ai" target="_blank" class="underline">OpenRouter</a>. Нужен API-ключ ниже.
          </p>
        </div>

        <div>
          <label class="label">API-ключ OpenRouter</label>
          <input
            v-model="form.llm_token"
            class="input font-mono text-sm"
            type="password"
            placeholder="sk-or-v1-..."
            autocomplete="off"
          />
          <p class="text-xs text-gray-400 mt-1">
            Получите ключ на <a href="https://openrouter.ai/keys" target="_blank" class="underline">openrouter.ai/keys</a>
          </p>
        </div>

        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="label mb-0">Системный промпт</label>
            <button
              v-if="!form.prompt"
              type="button"
              class="text-xs text-primary-600 hover:underline"
              @click="form.prompt = DEFAULT_PROMPT"
            >
              ✦ Вставить базовый
            </button>
          </div>
          <textarea v-model="form.prompt" class="input resize-none h-32" :placeholder="DEFAULT_PROMPT"></textarea>
        </div>
        <div class="flex items-center gap-3">
          <label class="label mb-0">Активен</label>
          <input type="checkbox" v-model="form.is_active" class="w-4 h-4 rounded" />
        </div>
        <div class="flex gap-3 pt-2">
          <button type="button" class="btn-secondary flex-1" @click="$emit('close')">Отмена</button>
          <button type="submit" class="btn-primary flex-1" :disabled="saving || deleting">
            {{ saving ? 'Сохраняю...' : 'Сохранить' }}
          </button>
        </div>
        <div class="border-t border-gray-100 pt-4 mt-2">
          <button
            type="button"
            class="w-full text-sm text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg px-3 py-2 transition-colors text-left"
            :disabled="deleting || saving"
            @click="handleDelete"
          >
            {{ deleting ? 'Удаляю...' : '🗑 Удалить агента' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAgentsStore } from '~/stores/agents'
import { useToastStore } from '~/stores/toast'

const DEFAULT_PROMPT = `Ты — умный и полезный ИИ-ассистент. Отвечай на русском языке, если пользователь пишет по-русски.

Твои принципы:
- Давай чёткие, конкретные и полезные ответы
- Если есть инструменты — используй их когда это уместно
- Будь вежлив и профессионален
- Если не знаешь ответа — скажи об этом честно`

const props = defineProps({ agent: { type: Object, required: true } })
const emit = defineEmits(['close', 'saved', 'deleted'])

const agentsStore = useAgentsStore()
const toast = useToastStore()
const saving = ref(false)
const deleting = ref(false)

const form = ref({
  name: props.agent.name,
  description: props.agent.description,
  llm_url: props.agent.llm_url,
  llm_model: props.agent.llm_model ?? '',
  llm_token: props.agent.llm_token ?? '',
  prompt: props.agent.prompt,
  is_active: props.agent.is_active,
})

async function handleDelete() {
  if (!confirm(`Удалить агента "${props.agent.name}"? Это действие необратимо.`)) return
  deleting.value = true
  try {
    await agentsStore.deleteAgent(props.agent.id)
    toast.success('Агент удалён')
    emit('deleted')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка удаления')
  } finally {
    deleting.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      description: form.value.description,
      llm_url: form.value.llm_url,
      llm_model: form.value.llm_model || null,
      llm_token: form.value.llm_token || null,
      prompt: form.value.prompt,
      is_active: form.value.is_active,
    }
    const updated = await agentsStore.updateAgent(props.agent.id, payload)
    toast.success('Агент обновлён')
    emit('saved', updated)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка сохранения')
  } finally {
    saving.value = false
  }
}
</script>
