<template>
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 bg-black/40 z-[100] flex items-center justify-center p-4" @click.self="$emit('close')">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 flex flex-col items-center text-center gap-4">
        <div class="w-14 h-14 rounded-full bg-orange-100 flex items-center justify-center text-3xl">🔧</div>
        <div>
          <h3 class="text-lg font-bold text-gray-900 mb-1">Технические работы</h3>
          <p class="text-sm text-gray-500">
            {{ label }} временно на техническом обслуживании и может работать некорректно.
            Подробнее можете узнать у менеджера.
          </p>
        </div>
        <div class="flex flex-col gap-2 w-full pt-1">
          <a
            href="https://t.me/ascnai_nocode"
            target="_blank"
            rel="noopener"
            class="w-full py-2.5 rounded-xl bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors text-center"
            @click="$emit('close')"
          >✉️ Написать в поддержку</a>
          <button
            class="w-full py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            @click="$emit('continue')"
          >Продолжить</button>
          <button
            class="w-full py-2.5 rounded-xl text-sm text-gray-400 hover:text-gray-600 transition-colors"
            @click="$emit('close')"
          >Назад</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  label: { type: String, default: 'Объект' },
})
defineEmits(['close', 'continue'])
</script>
