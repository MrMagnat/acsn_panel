<template>
  <div class="p-8 max-w-4xl">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Скиллы</h1>
      <p class="text-gray-500 text-sm mt-1">Каталог знаний и поведений — добавляйте скиллы к агентам в их настройках</p>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-400">Загрузка...</div>

    <div v-else-if="!skills.length" class="text-center py-16 text-gray-400">
      <div class="text-5xl mb-3">✨</div>
      <p class="font-medium">Скиллов пока нет</p>
      <p class="text-sm mt-1">Скоро здесь появятся готовые наборы знаний для ваших агентов</p>
    </div>

    <div v-else>
      <!-- Группировка по категориям -->
      <div v-for="(group, category) in groupedSkills" :key="category" class="mb-8">
        <h2 v-if="category" class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">{{ category }}</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div
            v-for="skill in group"
            :key="skill.id"
            class="card p-4 flex flex-col gap-2 hover:shadow-md transition-shadow"
          >
            <div class="flex items-start gap-3">
              <span class="text-3xl shrink-0">{{ skill.icon }}</span>
              <div class="min-w-0">
                <div class="flex items-center gap-1.5">
                  <div class="font-semibold text-gray-900 text-sm">{{ skill.name }}</div>
                  <a
                    v-if="skill.is_maintenance"
                    href="https://t.me/ascnai_nocode"
                    target="_blank"
                    rel="noopener"
                    class="text-orange-500 hover:text-orange-600 text-sm"
                    title="Скилл временно на тех.обслуживании и может работать некорректно — подробнее у менеджера"
                  >🔧</a>
                </div>
                <p v-if="skill.description" class="text-xs text-gray-500 mt-0.5 line-clamp-3">{{ skill.description }}</p>
              </div>
            </div>
            <div class="mt-auto pt-2 border-t border-gray-50">
              <p class="text-xs text-gray-400 italic">Добавьте скилл к агенту в его настройках</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { skillsApi } from '@/api/skills'

const skills = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await skillsApi.list()
    skills.value = res.data
  } catch { /* тихо */ } finally {
    loading.value = false
  }
})

const groupedSkills = computed(() => {
  const groups = {}
  for (const skill of skills.value) {
    const cat = skill.category || ''
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(skill)
  }
  return groups
})
</script>
