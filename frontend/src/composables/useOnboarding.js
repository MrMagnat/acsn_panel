import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { driver } from 'driver.js'
import 'driver.js/dist/driver.css'
import { onboardingApi } from '@/api/onboarding'

// Shared state (singleton)
const config = ref(null)
const showWelcome = ref(false)
const showVideo = ref(false)

export function useOnboarding() {
  const router = useRouter()

  async function loadConfig() {
    if (config.value) return
    try {
      const res = await onboardingApi.getConfig()
      config.value = res.data
    } catch {
      // Если не загрузилось — онбординг не показываем
    }
  }

  function isCompleted() {
    return localStorage.getItem('onboarding_done') === '1'
  }

  function checkAutoShow() {
    if (!isCompleted() && config.value?.enabled) {
      showWelcome.value = true
    }
  }

  function openWelcome() {
    showWelcome.value = true
  }

  function closeWelcome() {
    showWelcome.value = false
  }

  async function startTour() {
    showWelcome.value = false
    const steps = config.value?.steps
    if (!steps?.length) return

    let tourCompleted = false

    const driverSteps = steps.map((s) => ({
      element: s.element || undefined,
      popover: {
        title: s.title,
        description: buildDesc(s),
        side: s.side || 'bottom',
        align: 'start',
      },
    }))

    const driverObj = driver({
      showProgress: true,
      progressText: '{{current}} из {{total}}',
      nextBtnText: 'Далее →',
      prevBtnText: '← Назад',
      doneBtnText: 'Завершить ✓',
      allowClose: true,
      steps: driverSteps,

      onNextClick: async () => {
        const idx = driverObj.getActiveIndex()
        const isLast = idx === steps.length - 1
        if (isLast) {
          tourCompleted = true
          driverObj.destroy()
          return
        }
        await navigateTo(steps[idx + 1])
        driverObj.moveNext()
      },

      onPrevClick: async () => {
        const idx = driverObj.getActiveIndex()
        if (idx === 0) return
        await navigateTo(steps[idx - 1])
        driverObj.movePrevious()
      },

      onDestroyed: () => {
        localStorage.setItem('onboarding_done', '1')
        if (tourCompleted && config.value?.video_url) {
          showVideo.value = true
        }
      },
    })

    // Переходим к странице первого шага
    await navigateTo(steps[0])
    driverObj.drive()
  }

  async function navigateTo(step) {
    if (step.route && router.currentRoute.value.path !== step.route) {
      await router.push(step.route)
      await nextTick()
    }
    // Ждём появления элемента в DOM (страница может грузить данные асинхронно)
    if (step.element) {
      await waitForElement(step.element, 4000)
    } else {
      await sleep(200)
    }
  }

  async function waitForElement(selector, timeout = 4000) {
    const start = Date.now()
    while (Date.now() - start < timeout) {
      if (document.querySelector(selector)) return
      await sleep(100)
    }
  }

  function buildDesc(step) {
    let text = step.description || ''
    if (step.image_url) {
      text += `<br><img src="${step.image_url}" style="max-width:100%;border-radius:8px;margin-top:10px;">`
    }
    return text
  }

  function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms))
  }

  return {
    config,
    showWelcome,
    showVideo,
    loadConfig,
    checkAutoShow,
    openWelcome,
    closeWelcome,
    startTour,
  }
}
