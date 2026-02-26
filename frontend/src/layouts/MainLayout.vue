<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const sidebarVisible = ref(false)
const menuItems = computed(() => {
  const items = [
    { label: 'Inicio', icon: 'pi pi-home', to: '/' },
    { label: 'Notas', icon: 'pi pi-list', to: '/notas' },
    { label: 'Pendientes', icon: 'pi pi-clock', to: '/notas/pendientes' },
  ]
  // Solo roles con permiso ven "Atrasadas"
  if (
    auth.usuario?.rol &&
    ['ADMIN', 'DIRECTOR', 'JEFE', 'SOLO_LECTURA'].includes(auth.usuario.rol)
  ) {
    items.push({ label: 'Atrasadas', icon: 'pi pi-exclamation-triangle', to: '/notas/atrasadas' })
  }
  return items.map((item) => ({
    ...item,
    command: () => router.push(item.to),
  }))
})

function irA(ruta) {
  router.push(ruta)
}

async function cerrarSesion() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <!-- Header superior -->
    <header
      class="h-14 flex items-center justify-between px-4 shadow-sm sticky top-0 z-20"
      style="background: var(--color-primario); color: white"
    >
      <div class="flex items-center gap-3">
        <Button
          icon="pi pi-bars"
          text
          rounded
          class="text-white lg:hidden"
          aria-label="Abrir menú"
          @click="sidebarVisible = !sidebarVisible"
        />
        <span class="font-semibold text-lg">Gestor de Notas - RRHH</span>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-sm hidden sm:inline">{{
          auth.nombreCompleto || auth.usuario?.username
        }}</span>
        <Avatar
          :label="(auth.nombreCompleto || auth.usuario?.username || 'U').charAt(0).toUpperCase()"
          class="bg-white text-primario"
          style="background: var(--color-acento) !important; color: var(--color-primario)"
        />
        <Button
          icon="pi pi-sign-out"
          text
          rounded
          severity="secondary"
          class="text-white"
          @click="cerrarSesion"
        />
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar móvil (drawer) -->
      <Sidebar v-model:visible="sidebarVisible" position="left" class="w-64 lg:!hidden">
        <template #header>
          <span class="font-semibold text-gray-800">Menú</span>
        </template>
        <nav class="flex flex-col gap-1 py-2">
          <router-link
            v-for="item in menuItems"
            :key="item.to"
            :to="item.to"
            class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100"
            :class="route.path === item.to ? 'bg-primario/10 font-medium' : ''"
            style="--color-primario: var(--color-primario)"
            @click="sidebarVisible = false"
          >
            <i :class="['pi', item.icon]"></i>
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
      </Sidebar>

      <!-- Sidebar desktop (persistente) -->
      <aside
        class="hidden lg:flex lg:flex-col w-64 border-r border-gray-200 bg-white flex-shrink-0"
      >
        <div class="p-4 border-b border-gray-100">
          <span class="font-semibold text-gray-800">Menú</span>
        </div>
        <nav class="flex flex-col gap-1 p-2">
          <router-link
            v-for="item in menuItems"
            :key="item.to"
            :to="item.to"
            class="flex items-center gap-3 px-3 py-2 rounded-lg transition-colors"
            :class="
              route.path === item.to
                ? 'bg-gray-100 font-medium text-primario'
                : 'text-gray-700 hover:bg-gray-50'
            "
          >
            <i :class="['pi', item.icon]"></i>
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
      </aside>

      <!-- Contenido principal -->
      <main class="flex-1 overflow-auto bg-gray-50">
        <div class="p-4 lg:p-6">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>
