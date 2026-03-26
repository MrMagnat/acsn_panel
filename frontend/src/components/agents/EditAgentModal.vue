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

        <!-- Языковая модель (OpenRouter) -->
        <div>
          <label class="label">Языковая модель</label>
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
          <label class="label">Системный промпт</label>
          <textarea v-model="form.prompt" class="input resize-none h-24" placeholder="Ты — полезный ассистент..."></textarea>
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
import { useAgentsStore } from '@/stores/agents'
import { useToastStore } from '@/stores/toast'

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
