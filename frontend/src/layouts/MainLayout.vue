<script setup>
/**
 * MainLayout — Menú lateral por rol.
 * SUPERVISOR/ADMINISTRADOR: Inicio, Notas, Sin asignar (si hay), Administración (solo ADMIN)
 * OPERADOR: Inicio, Mi Trabajo, Notas
 * CONSULTOR: Inicio, Notas
 */
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { get } from '@/api/cliente'
import { COLORES_ESTADO, LABELS_ESTADO } from '@/utils/notas'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const sidebarVisible = ref(false)

// Búsqueda global en navbar (solo visible si el usuario está autenticado)
const busquedaExpandida = ref(false)
const inputBusqueda = ref(null)
const busquedaGlobal = ref('')
const resultados = ref([])
const mostrarResultados = ref(false)
const buscando = ref(false)
let timeoutBusqueda = null

/** Búsqueda con debounce de 300ms contra /api/notas/?search= */
function onBusqueda() {
  clearTimeout(timeoutBusqueda)
  if (busquedaGlobal.value.length < 2) {
    resultados.value = []
    mostrarResultados.value = false
    return
  }
  buscando.value = true
  mostrarResultados.value = true
  timeoutBusqueda = setTimeout(async () => {
    try {
      const res = await get(
        `/api/notas/?search=${encodeURIComponent(busquedaGlobal.value)}`,
      )
      const lista = Array.isArray(res) ? res : res?.results || []
      resultados.value = lista.slice(0, 5)
    } catch {
      resultados.value = []
    } finally {
      buscando.value = false
    }
  }, 300)
}

function irANota(id) {
  router.push(`/notas/${id}`)
  cerrarBusqueda()
}

function irAResultados() {
  if (busquedaGlobal.value.length >= 2) {
    router.push(`/notas?search=${encodeURIComponent(busquedaGlobal.value)}`)
    cerrarBusqueda()
  }
}

/** Colapsar el buscador, limpiar texto y resultados */
function cerrarBusqueda() {
  busquedaExpandida.value = false
  busquedaGlobal.value = ''
  mostrarResultados.value = false
  resultados.value = []
}

// Focus automático en el input cuando se expande
watch(busquedaExpandida, (val) => {
  if (val) nextTick(() => inputBusqueda.value?.focus())
})

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
    // Usuarios y Administración: solo ADMINISTRADOR
    if (rol === 'ADMINISTRADOR') {
      items.push({ label: 'Usuarios', icon: 'pi pi-users', to: '/usuarios' })
      items.push({ label: 'Sectores', icon: 'pi pi-building', to: '/sectores' })
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

onMounted(() => {
  cargarNotasSinAsignar()
  // Cerrar y colapsar búsqueda al hacer click fuera
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.busqueda-global')) {
      cerrarBusqueda()
    }
  })
})
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

      <!-- Barra de búsqueda global colapsable (solo visible si el usuario está autenticado) -->
      <div v-if="auth.usuario" class="busqueda-global relative flex items-center">
        <!-- Ícono lupa siempre visible -->
        <button
          type="button"
          class="p-2 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
          aria-label="Buscar nota"
          @click="busquedaExpandida = !busquedaExpandida"
        >
          <i class="pi pi-search text-sm" />
        </button>

        <!-- Input expandible con transición -->
        <transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="w-0 opacity-0"
          enter-to-class="w-64 opacity-100"
          leave-active-class="transition-all duration-200 ease-in"
          leave-from-class="w-64 opacity-100"
          leave-to-class="w-0 opacity-0"
        >
          <div
            v-if="busquedaExpandida"
            class="relative overflow-hidden"
          >
            <i
              class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-300 z-10 text-sm"
            />
            <input
              ref="inputBusqueda"
              v-model="busquedaGlobal"
              type="text"
              placeholder="Buscar nota..."
              class="w-64 pl-9 pr-4 py-1.5 rounded-lg text-sm bg-white/10 text-white placeholder-gray-300 border border-white/20 focus:outline-none focus:bg-white/20 transition-all"
              @input="onBusqueda"
              @keydown.enter="irAResultados"
              @keydown.escape="cerrarBusqueda"
            />
          </div>
        </transition>

        <!-- Dropdown de resultados rápidos -->
        <div
          v-if="mostrarResultados && resultados.length > 0"
          class="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-80 overflow-y-auto"
        >
          <div
            v-for="nota in resultados"
            :key="nota.id"
            class="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0"
            @click="irANota(nota.id)"
          >
            <div>
              <p class="font-mono text-xs text-[#1e3a5f] font-bold">
                {{ nota.numero_nota }}
              </p>
              <p class="text-sm text-gray-700 truncate max-w-xs">
                {{ nota.tema }}
              </p>
            </div>
            <span
              class="px-2 py-0.5 rounded-full text-xs text-white ml-2 shrink-0"
              :style="{ backgroundColor: COLORES_ESTADO[nota.estado] }"
            >
              {{ LABELS_ESTADO[nota.estado] }}
            </span>
          </div>

          <div
            v-if="resultados.length === 5"
            class="px-4 py-2 text-center text-sm text-[#1e3a5f] hover:bg-gray-50 cursor-pointer font-medium"
            @click="irAResultados"
          >
            Ver todos los resultados →
          </div>
        </div>

        <!-- Sin resultados -->
        <div
          v-if="
            mostrarResultados &&
            busquedaGlobal.length >= 2 &&
            resultados.length === 0 &&
            !buscando
          "
          class="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-50 px-4 py-3"
        >
          <p class="text-sm text-gray-500">
            No se encontraron notas para "{{ busquedaGlobal }}"
          </p>
        </div>
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
