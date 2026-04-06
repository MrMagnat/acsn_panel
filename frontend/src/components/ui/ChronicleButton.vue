<template>
  <button
    class="chronicleButton"
    :class="{ outlined }"
    :style="btnStyle"
    type="button"
    @click="$emit('click')"
  >
    <span><em>{{ text }}</em></span>
    <span><em>{{ text }}</em></span>
  </button>
</template>

<script setup>
import { computed, onMounted } from 'vue'

const props = defineProps({
  text: { type: String, required: true },
  hoverColor: { type: String, default: '#a594fd' },
  width: { type: String, default: '160px' },
  outlined: { type: Boolean, default: false },
  borderRadius: { type: String, default: '8px' },
  customBackground: { type: String, default: '#fff' },
  customForeground: { type: String, default: '#111014' },
  hoverForeground: { type: String, default: '#111014' },
})
defineEmits(['click'])

const btnStyle = computed(() => ({
  '--chronicle-button-background': props.customBackground,
  '--chronicle-button-foreground': props.customForeground,
  '--chronicle-button-hover-background': props.hoverColor,
  '--chronicle-button-hover-foreground': props.hoverForeground,
  '--chronicle-button-border-radius': props.borderRadius,
  width: props.width,
  borderRadius: props.borderRadius,
}))

onMounted(() => {
  if (document.getElementById('chronicle-button-style')) return
  const style = document.createElement('style')
  style.id = 'chronicle-button-style'
  style.innerHTML = `
.chronicleButton {
  --chronicle-button-border-radius: 8px;
  border-radius: var(--chronicle-button-border-radius);
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
  line-height: 1;
  padding: 0.75rem 1rem;
  cursor: pointer;
  border: none;
  font-weight: 700;
  font-size: 0.875rem;
  background: var(--chronicle-button-background);
  color: var(--chronicle-button-foreground);
  transition: background 0.4s linear, color 0.4s linear;
  will-change: background, color;
  position: relative;
}
.chronicleButton:hover {
  background: var(--chronicle-button-hover-background);
  color: var(--chronicle-button-hover-foreground);
}
.chronicleButton span {
  position: relative;
  display: block;
  perspective: 108px;
}
.chronicleButton span:nth-of-type(2) { position: absolute; }
.chronicleButton em {
  font-style: normal;
  display: inline-block;
  color: inherit;
  will-change: transform, opacity;
  transition: transform 0.55s cubic-bezier(.645,.045,.355,1), opacity 0.35s linear 0.2s;
}
.chronicleButton span:nth-of-type(1) em { transform-origin: top; }
.chronicleButton span:nth-of-type(2) em {
  opacity: 0;
  transform: rotateX(-90deg) scaleX(.9) translate3d(0,10px,0);
  transform-origin: bottom;
}
.chronicleButton:hover span:nth-of-type(1) em {
  opacity: 0;
  transform: rotateX(90deg) scaleX(.9) translate3d(0,-10px,0);
}
.chronicleButton:hover span:nth-of-type(2) em {
  opacity: 1;
  transform: rotateX(0deg) scaleX(1) translateZ(0);
  transition: transform 0.75s cubic-bezier(.645,.045,.355,1), opacity 0.35s linear 0.3s;
}
.chronicleButton.outlined {
  background: transparent;
  border: 2px solid var(--chronicle-button-background);
  padding: calc(0.75rem - 2px) 1rem;
  color: var(--chronicle-button-background);
  transition: border 0.4s linear, color 0.4s linear;
}
.chronicleButton.outlined:hover {
  border-color: var(--chronicle-button-hover-background);
  color: var(--chronicle-button-hover-background);
}
`
  document.head.appendChild(style)
})
</script>
