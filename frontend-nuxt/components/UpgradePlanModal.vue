<template>
  <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-8 flex flex-col items-center text-center">
      <div class="w-16 h-16 rounded-full bg-yellow-100 flex items-center justify-center text-3xl mb-5">
        🔒
      </div>
      <h2 class="text-xl font-bold text-gray-900 mb-2">{{ title }}</h2>
      <p class="text-sm text-gray-500 mb-6">{{ description }}</p>
      <a
        href="https://ascn.ai/pricing"
        target="_blank"
        rel="noopener"
        class="w-full btn-primary text-center py-3 text-sm font-semibold mb-3"
      >
        Повысить тариф →
      </a>
      <button class="text-sm text-gray-400 hover:text-gray-600" @click="$emit('close')">
        Отмена
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: 'Лимит агентов достигнут' },
  description: {
    type: String,
    default: 'На вашем тарифе недоступно добавление новых агентов. Повысьте тариф, чтобы создавать больше ИИ-агентов.',
  },
})
defineEmits(['close'])
</script>
