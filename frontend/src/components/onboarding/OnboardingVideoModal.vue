<template>
  <Teleport to="body">
    <div class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" @click.self="$emit('close')">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h2 class="font-semibold text-gray-900">🎥 Полное видео-руководство</h2>
            <p class="text-xs text-gray-400 mt-0.5">Посмотрите как платформа работает на практике</p>
          </div>
          <button class="text-gray-400 hover:text-gray-600 text-xl" @click="$emit('close')">✕</button>
        </div>

        <div class="p-6">
          <div v-if="embedUrl" class="aspect-video rounded-xl overflow-hidden bg-gray-100">
            <iframe
              :src="embedUrl"
              class="w-full h-full"
              allowfullscreen
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            ></iframe>
          </div>
          <div v-else class="aspect-video rounded-xl bg-gray-100 flex items-center justify-center text-gray-400 text-sm">
            Видео не добавлено
          </div>

          <div class="flex gap-3 mt-4">
            <button class="btn-primary flex-1 justify-center" @click="$emit('close')">
              Начать работу →
            </button>
            <a
              href="https://t.me/ascnai_nocode"
              target="_blank"
              class="btn-secondary flex-1 justify-center flex items-center gap-2"
            >
              💬 Поддержка
            </a>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  videoUrl: { type: String, default: '' },
})
defineEmits(['close'])

const embedUrl = computed(() => {
  const url = props.videoUrl
  if (!url) return ''
  // YouTube
  const ytMatch = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/)
  if (ytMatch) return `https://www.youtube.com/embed/${ytMatch[1]}?autoplay=1`
  // Vimeo
  const vmMatch = url.match(/vimeo\.com\/(\d+)/)
  if (vmMatch) return `https://player.vimeo.com/video/${vmMatch[1]}?autoplay=1`
  // Прямая ссылка
  return url
})
</script>
