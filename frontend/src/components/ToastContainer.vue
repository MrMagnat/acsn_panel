<template>
  <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toastStore.toasts"
        :key="toast.id"
        class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium min-w-[280px] max-w-sm"
        :class="toastClass(toast.type)"
      >
        <span class="text-lg">{{ toastIcon(toast.type) }}</span>
        <span>{{ toast.message }}</span>
        <button class="ml-auto opacity-60 hover:opacity-100" @click="toastStore.remove(toast.id)">✕</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useToastStore } from '@/stores/toast'

const toastStore = useToastStore()

function toastClass(type) {
  return {
    success: 'bg-green-50 text-green-800 border border-green-200',
    error: 'bg-red-50 text-red-800 border border-red-200',
    info: 'bg-blue-50 text-blue-800 border border-blue-200',
  }[type] || 'bg-gray-50 text-gray-800 border border-gray-200'
}

function toastIcon(type) {
  return { success: '✓', error: '✗', info: 'ℹ' }[type] || 'ℹ'
}
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(100%); }
.toast-leave-to  { opacity: 0; transform: translateX(100%); }
</style>
