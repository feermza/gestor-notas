<script setup>
/**
 * MainLayout — Menú lateral por rol.
 * SUPERVISOR/ADMINISTRADOR: Inicio, Notas, Sin asignar (si hay), Administración (solo ADMIN)
 * OPERADOR: Inicio, Mi Trabajo, Notas
 * CONSULTOR: Inicio, Notas
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { get } from '@/api/cliente'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const sidebarVisible = ref(false)

// Solo para SUPERVISOR/ADMIN: si hay notas INGRESADA sin responsable, mostrar "Sin asignar"
const hayNotasSinAsignar = ref(false)

async function cargarNotasSinAsignar() {
  if (!auth.usuario || !['SUPERVISOR', 'ADMINISTRADOR'].includes(auth.usuario.rol)) return
  try {
    const res = await get('/api/notas/?estado=INGRESADA')
    const lista = Array.isArray(res) ? res : res?.results || []
    hayNotasSinAsignar.value = lista.some((n) => !n.responsable || !n.responsable.id)
  } catch {
    hayNotasSinAsignar.value = false
  }
}

const menuItems = computed(() => {
  const rol = auth.usuario?.rol
  const items = []

  // Todos los roles ven Inicio
  items.push({ label: 'Inicio', icon: 'pi pi-home', to: '/' })

  // SUPERVISOR / ADMINISTRADOR
  if (rol === 'SUPERVISOR' || rol === 'ADMINISTRADOR') {
    items.push({ label: 'Notas', icon: 'pi pi-list', to: '/notas' })
    // Sin asignar: visible solo si hay notas sin asignar
    if (hayNotasSinAsignar.value) {
      items.push({ label: 'Sin asignar', icon: 'pi pi-inbox', to: '/notas?estado=INGRESADA' })
    }
    // Administración: solo ADMINISTRADOR
    if (rol === 'ADMINISTRADOR') {
      items.push({ label: 'Administración', icon: 'pi pi-cog', to: '/admin' })
    }
    return items
  }

  // OPERADOR
  if (rol === 'OPERADOR') {
    items.push({ label: 'Mi Trabajo', icon: 'pi pi-briefcase', to: '/mi-trabajo' })
    items.push({ label: 'Notas', icon: 'pi pi-list', to: '/notas' })
    return items
  }

  // CONSULTOR (y cualquier otro rol por defecto)
  items.push({ label: 'Notas', icon: 'pi pi-list', to: '/notas' })
  return items
})

// Clase activa: comparar fullPath para links con query
function esActivo(item) {
  if (route.fullPath === item.to) return true
  // Para /notas sin query, considerar activo si path es /notas
  if (item.to === '/notas' && route.path === '/notas' && !route.query.estado && !route.query.atrasadas && !route.query.sin_asignar) return true
  return false
}

async function cerrarSesion() {
  await auth.logout()
  router.push('/login')
}

onMounted(cargarNotasSinAsignar)
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
            :class="esActivo(item) ? 'bg-primario/10 font-medium' : ''"
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
              esActivo(item)
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
