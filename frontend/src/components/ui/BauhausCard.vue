<template>
  <div
    ref="cardRef"
    class="bauhaus-card"
    :style="cardStyle"
  >
    <!-- Header -->
    <div class="bauhaus-card-header">
      <div class="bauhaus-date">{{ topInscription }}</div>
      <div class="bauhaus-dots" @click.stop="$emit('more', id)">
        <svg viewBox="0 0 24 24" fill="currentColor" class="bauhaus-size6">
          <path fill-rule="evenodd" d="M10.5 6a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0Zm0 6a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0Zm0 6a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0Z" clip-rule="evenodd" />
        </svg>
      </div>
    </div>

    <!-- Body -->
    <div class="bauhaus-card-body">
      <h3>{{ mainText }}</h3>
      <p>{{ subMainText }}</p>
      <div class="bauhaus-progress">
        <span>{{ progressLabel }}</span>
        <div class="bauhaus-progress-bar">
          <div :style="{ width: clampedProgress + '%', backgroundColor: accentColor }" />
        </div>
        <span>{{ progressValue }}</span>
      </div>
    </div>

    <!-- Footer -->
    <div class="bauhaus-card-footer">
      <div class="bauhaus-button-container">
        <ChronicleButton
          :text="primaryLabel"
          width="110px"
          :hover-color="accentColor"
          :custom-background="chronicleButtonBg"
          :custom-foreground="chronicleButtonFg"
          :hover-foreground="chronicleButtonHoverFg"
          :border-radius="borderRadius"
          @click.stop="$emit('primary', id)"
        />
        <ChronicleButton
          :text="secondaryLabel"
          width="110px"
          :outlined="true"
          :hover-color="accentColor"
          :custom-background="chronicleButtonBg"
          :custom-foreground="chronicleButtonFg"
          :hover-foreground="chronicleButtonHoverFg"
          :border-radius="borderRadius"
          @click.stop="$emit('secondary', id)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import ChronicleButton from './ChronicleButton.vue'

const props = defineProps({
  id: { type: String, required: true },
  accentColor: { type: String, default: '#156ef6' },
  backgroundColor: { type: String, default: 'var(--bauhaus-card-bg)' },
  separatorColor: { type: String, default: 'var(--bauhaus-card-separator)' },
  borderRadius: { type: String, default: '2em' },
  borderWidth: { type: String, default: '2px' },
  topInscription: { type: String, default: '' },
  mainText: { type: String, default: '' },
  subMainText: { type: String, default: '' },
  progressLabel: { type: String, default: 'Инструменты:' },
  progress: { type: Number, default: 0 },
  progressValue: { type: String, default: '0' },
  primaryLabel: { type: String, default: 'Открыть' },
  secondaryLabel: { type: String, default: 'Настройки' },
  chronicleButtonBg: { type: String, default: 'var(--bauhaus-chronicle-bg)' },
  chronicleButtonFg: { type: String, default: 'var(--bauhaus-chronicle-fg)' },
  chronicleButtonHoverFg: { type: String, default: 'var(--bauhaus-chronicle-hover-fg)' },
})
defineEmits(['primary', 'secondary', 'more'])

const cardRef = ref(null)
const clampedProgress = computed(() => Math.min(100, Math.max(0, props.progress)))

const cardStyle = computed(() => ({
  '--card-bg': props.backgroundColor,
  '--card-accent': props.accentColor,
  '--card-radius': props.borderRadius,
  '--card-border-width': props.borderWidth,
  '--card-separator': props.separatorColor,
}))

function onMouseMove(e) {
  const card = cardRef.value
  if (!card) return
  const rect = card.getBoundingClientRect()
  const x = e.clientX - rect.left - rect.width / 2
  const y = e.clientY - rect.top - rect.height / 2
  card.style.setProperty('--rotation', Math.atan2(-x, y) + 'rad')
}

onMounted(() => {
  cardRef.value?.addEventListener('mousemove', onMouseMove)

  if (document.getElementById('bauhaus-card-styles')) return
  const style = document.createElement('style')
  style.id = 'bauhaus-card-styles'
  style.innerHTML = `
.bauhaus-card {
  position: relative;
  z-index: 0;
  width: 100%;
  min-height: 13rem;
  display: grid;
  place-content: center;
  place-items: center;
  text-align: center;
  box-shadow: 1px 8px 20px rgb(0,0,0/18%);
  border-radius: var(--card-radius, 2em);
  border: var(--card-border-width, 2px) solid transparent;
  --rotation: 4.2rad;
  background-image:
    linear-gradient(var(--card-bg, #151419), var(--card-bg, #151419)),
    linear-gradient(calc(var(--rotation, 4.2rad)), var(--card-accent, #156ef6) 0, var(--card-bg, #151419) 30%, transparent 80%);
  background-origin: border-box;
  background-clip: padding-box, border-box;
  color: var(--bauhaus-card-inscription-main, #f0f0f1);
  transition: box-shadow 0.2s;
  cursor: pointer;
}
.bauhaus-card:hover {
  box-shadow: 1px 12px 28px rgb(0,0,0/28%);
}
.bauhaus-card-header {
  position: absolute;
  top: 0; left: 0; right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.9em 0.75em 0 1.25em;
}
.bauhaus-date {
  font-size: 0.75rem;
  color: var(--bauhaus-card-inscription-top, #bfc7d5);
}
.bauhaus-dots {
  color: var(--bauhaus-card-inscription-main, #f0f0f1);
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s;
}
.bauhaus-dots:hover { opacity: 1; }
.bauhaus-size6 { width: 1.25rem; }
.bauhaus-card-body {
  position: absolute;
  width: 100%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 0.5em 1.25em;
}
.bauhaus-card-body h3 {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 0.25em;
  color: var(--bauhaus-card-inscription-main, #f0f0f1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bauhaus-card-body p {
  font-size: 0.8rem;
  color: var(--bauhaus-card-inscription-sub, #a0a1b3);
  margin-bottom: 0;
}
.bauhaus-progress { margin-top: 0.75rem; }
.bauhaus-progress-bar {
  position: relative;
  width: 100%;
  background: var(--bauhaus-card-progress-bar-bg, #363636);
  height: 4px;
  border-radius: 50px;
  overflow: hidden;
}
.bauhaus-progress-bar > div {
  height: 4px;
  border-radius: 50px;
  transition: width 0.4s ease;
}
.bauhaus-progress span:first-of-type {
  font-size: 0.7rem;
  font-weight: 600;
  display: block;
  margin-bottom: 0.3em;
  text-align: left;
  color: var(--bauhaus-card-inscription-progress-label, #b4c7e7);
}
.bauhaus-progress span:last-of-type {
  font-size: 0.7rem;
  display: block;
  margin-top: 0.3em;
  text-align: right;
  color: var(--bauhaus-card-inscription-progress-value, #e7e7f7);
}
.bauhaus-card-footer {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0.6em 1em;
  border-top: 1px solid var(--card-separator, #2F2B2A);
}
.bauhaus-button-container {
  display: flex;
  gap: 10px;
}
`
  document.head.appendChild(style)
})

onUnmounted(() => {
  cardRef.value?.removeEventListener('mousemove', onMouseMove)
})
</script>
