<template>
  <Teleport to="body">
    <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8 text-center">
        <div class="text-6xl mb-4">🤖</div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Добро пожаловать в ASCN!</h2>
        <p class="text-gray-500 mb-2">Обучение займёт всего <strong class="text-gray-700">2–3 минуты</strong> —</p>
        <p class="text-gray-500 mb-8">и вы сможете получать результаты от ИИ-агентов прямо сейчас.</p>

        <div class="space-y-3">
          <button
            class="btn-primary w-full justify-center text-base py-3"
            @click="$emit('start')"
          >
            🎓 Пройти обучение
          </button>
          <a
            :href="supportUrl"
            target="_blank"
            class="btn-secondary w-full justify-center flex items-center gap-2 text-base py-3"
          >
            💬 Написать в поддержку
          </a>
          <button
            class="text-sm text-gray-400 hover:text-gray-600 w-full py-2 transition-colors"
            @click="$emit('skip')"
          >
            Пропустить
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  supportUrl: {
    type: String,
    default: 'https://t.me/ascnai_nocode',
  },
})
defineEmits(['start', 'skip'])
</script>
