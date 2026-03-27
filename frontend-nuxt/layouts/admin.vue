<template>
  <div class="min-h-screen flex bg-surface">
    <aside class="w-56 bg-white border-r border-gray-100 flex flex-col shrink-0">
      <div class="px-6 py-5 border-b border-gray-100">
        <span class="text-xl font-bold text-purple-600">ASCN</span>
        <span class="text-xs text-gray-400 ml-1">Admin</span>
      </div>
      <nav class="flex-1 px-3 py-4 space-y-1">
        <NuxtLink to="/admin/users" class="nav-link" active-class="nav-link--active">
          <span>👥</span> Пользователи
        </NuxtLink>
        <NuxtLink to="/admin/agents" class="nav-link" active-class="nav-link--active">
          <span>🤖</span> Агенты
        </NuxtLink>
        <NuxtLink to="/admin/tools" class="nav-link" active-class="nav-link--active">
          <span>🔧</span> Инструменты
        </NuxtLink>
        <div class="border-t border-gray-100 my-2"></div>
        <NuxtLink to="/cabinet/office" class="nav-link text-gray-400">
          <span>←</span> Личный кабинет
        </NuxtLink>
      </nav>
    </aside>
    <main class="flex-1 overflow-auto">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.nav-link {
  @apply flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors;
}
.nav-link--active {
  @apply bg-purple-50 text-purple-700 font-medium;
}
</style>
