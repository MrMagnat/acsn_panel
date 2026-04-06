<template>
  <BauhausCard
    :id="agent.id"
    :accent-color="agent.is_active ? '#156ef6' : '#6b7280'"
    :top-inscription="agent.is_active ? 'Активен' : 'Неактивен'"
    :main-text="agent.name"
    :sub-main-text="agent.description || ' '"
    progress-label="Инструменты:"
    :progress="toolsProgress"
    :progress-value="toolsProgressLabel"
    primary-label="Открыть"
    secondary-label="Запустить"
    @primary="$emit('click')"
    @secondary="$emit('click')"
    @more="$emit('click')"
  />
</template>

<script setup>
import { computed } from 'vue'
import BauhausCard from '@/components/ui/BauhausCard.vue'

const props = defineProps({
  agent: { type: Object, required: true },
  maxTools: { type: Number, default: 5 },
})
defineEmits(['click'])

const toolsProgress = computed(() =>
  props.maxTools > 0 ? Math.round((props.agent.tools_count / props.maxTools) * 100) : 0
)
const toolsProgressLabel = computed(() =>
  `${props.agent.tools_count} / ${props.maxTools}`
)
</script>
