<script setup>
/**
 * MainLayout — Menú lateral por rol.
 * SUPERVISOR/ADMINISTRADOR: Inicio, General, Sin asignar, Administración (solo ADMIN)
 * OPERADOR: Inicio, Asignadas, General
 * CONSULTOR: Inicio, Notas
 */
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { get } from '@/api/cliente'
import BadgeEstado from '@/components/BadgeEstado.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const sidebarVisible = ref(false)
const sidebarColapsado = ref(localStorage.getItem('sidebar-collapsed') === 'true')

function toggleSidebar() {
  if (window.innerWidth < 1024) {
    sidebarVisible.value = !sidebarVisible.value
    return
  }
  sidebarColapsado.value = !sidebarColapsado.value
  localStorage.setItem('sidebar-collapsed', String(sidebarColapsado.value))
}

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

const menuItems = computed(() => {
  const rol = auth.usuario?.rol
  const items = []

  // Todos los roles ven Inicio
  items.push({ label: 'Inicio', icon: 'pi pi-home', to: '/' })

  // SUPERVISOR / ADMINISTRADOR
  if (rol === 'SUPERVISOR' || rol === 'ADMINISTRADOR') {
    items.push({ type: 'section', label: 'NOTAS' })
    items.push({ label: 'General', icon: 'pi pi-list', to: '/notas' })
    items.push({
      label: 'Sin Asignar',
      icon: 'pi pi-inbox',
      to: '/notas',
      query: { estado: 'INGRESADA' },
      sinAsignar: true,
    })
    // Usuarios y Administración: solo ADMINISTRADOR
    if (rol === 'ADMINISTRADOR') {
      items.push({ type: 'section', label: 'SISTEMA' })
      items.push({ label: 'Usuarios', icon: 'pi pi-users', to: '/usuarios' })
      items.push({ label: 'Sectores', icon: 'pi pi-building', to: '/sectores' })
      items.push({ label: 'Administración', icon: 'pi pi-cog', to: '/admin' })
    }
    return items
  }

  // OPERADOR
  if (rol === 'OPERADOR') {
    items.push({ type: 'section', label: 'NOTAS' })
    items.push({ label: 'Asignadas', icon: 'pi pi-briefcase', to: '/mis-notas' })
    items.push({ label: 'General', icon: 'pi pi-list', to: '/notas' })
    return items
  }

  // CONSULTOR (y cualquier otro rol por defecto)
  items.push({ type: 'section', label: 'NOTAS' })
  items.push({ label: 'General', icon: 'pi pi-list', to: '/notas' })
  return items
})

/** Destino del router-link (combina `to` + `query` del ítem). */
function linkTo(item) {
  if (item.type === 'section') return '/'
  if (item.query && typeof item.to === 'string') {
    return { path: item.to, query: item.query }
  }
  return item.to
}

function esActivo(item) {
  if (item.type === 'section') return false
  if (item.sinAsignar) {
    return (
      route.path === '/notas' &&
      (route.query.estado === 'INGRESADA' || route.query.sin_asignar === 'true')
    )
  }
  if (item.to === '/notas' && !item.sinAsignar) {
    return (
      route.path === '/notas' &&
      route.query.estado !== 'INGRESADA' &&
      route.query.sin_asignar !== 'true'
    )
  }
  return route.path === item.to
}

function itemMenuKey(item) {
  if (item.type === 'section') return `section-${item.label}`
  if (item.sinAsignar) return 'menu-sin-asignar'
  if (typeof item.to === 'string') return item.to
  return item.to.path || 'menu-item'
}

const mostrarScrollTop = ref(false)
const mainContent = ref(null)

function onMainContentScroll() {
  const el = mainContent.value
  mostrarScrollTop.value = (el?.scrollTop ?? 0) > 300
}

function scrollToTop() {
  mainContent.value?.scrollTo({ top: 0, behavior: 'smooth' })
}

async function cerrarSesion() {
  await auth.logout()
  router.push('/login')
}

onMounted(() => {
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.busqueda-global')) {
      cerrarBusqueda()
    }
  })
  nextTick(() => {
    const el = mainContent.value
    if (el) {
      el.addEventListener('scroll', onMainContentScroll, { passive: true })
      onMainContentScroll()
    }
  })
})

onUnmounted(() => {
  mainContent.value?.removeEventListener('scroll', onMainContentScroll)
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
          class="text-white"
          aria-label="Abrir menú"
          @click="toggleSidebar"
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
            class="flex items-center justify-between px-4 py-3 hover:bg-[#d2d7e4] cursor-pointer border-b border-gray-100 last:border-0 transition-colors"
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
            <span class="ml-2 shrink-0">
              <BadgeEstado :estado="nota.estado" />
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
          <template v-for="item in menuItems" :key="itemMenuKey(item)">
            <p
              v-if="item.type === 'section'"
              class="px-3 pt-4 pb-1 text-xs font-semibold text-[#64748b] uppercase tracking-wider"
            >
              {{ item.label }}
            </p>
            <router-link
              v-else
              :to="linkTo(item)"
              custom
              v-slot="{ href, navigate }"
            >
              <a
                :href="href"
                class="menu-item-lateral flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-[#d2d7e4]"
                :class="{ activo: esActivo(item) }"
                style="--color-primario: var(--color-primario)"
                @click="
                  (e) => {
                    navigate(e)
                    sidebarVisible = false
                  }
                "
              >
                <i :class="item.icon"></i>
                <span>{{ item.label }}</span>
              </a>
            </router-link>
          </template>
        </nav>
      </Sidebar>

      <!-- Sidebar desktop (persistente) -->
      <aside
        class="hidden lg:flex lg:flex-col border-r border-gray-200 bg-[#eef2f7] flex-shrink-0 transition-all duration-200"
        :style="{ width: sidebarColapsado ? '64px' : '250px' }"
      >
        <div class="p-4 border-b-2 border-[#d2d7e4] flex items-center justify-center">
          <span v-show="!sidebarColapsado" class="font-semibold text-gray-800">Menú</span>
        </div>
        <nav class="flex flex-col gap-1 p-2">
          <template v-for="item in menuItems" :key="`desk-${itemMenuKey(item)}`">
            <p
              v-if="item.type === 'section'"
              v-show="!sidebarColapsado"
              class="px-3 pt-4 pb-1 text-xs font-semibold text-[#64748b] uppercase tracking-wider"
            >
              {{ item.label }}
            </p>
            <router-link
              v-else
              :to="linkTo(item)"
              custom
              v-slot="{ href, navigate }"
            >
              <a
                :href="href"
                v-tooltip.right="sidebarColapsado ? item.label : null"
                class="menu-item-lateral flex items-center gap-3 py-2 rounded-lg transition-colors"
                :class="[
                  sidebarColapsado ? 'justify-center px-0' : 'justify-start px-3',
                  { activo: esActivo(item) },
                  !esActivo(item) ? 'text-gray-700 hover:bg-[#d2d7e4]' : '',
                ]"
                @click="(e) => navigate(e)"
              >
                <i :class="item.icon"></i>
                <span v-show="!sidebarColapsado">{{ item.label }}</span>
              </a>
            </router-link>
          </template>
        </nav>
      </aside>

      <!-- Contenido principal -->
      <main ref="mainContent" class="flex-1 overflow-auto bg-gray-50">
        <div class="p-4 lg:p-6">
          <router-view />
        </div>
      </main>
    </div>

    <Transition name="fade">
      <button
        v-if="mostrarScrollTop"
        type="button"
        aria-label="Volver arriba"
        class="fixed bottom-6 right-6 z-40 w-10 h-10 rounded-full bg-[#1e3a5f] text-white flex items-center justify-center shadow-lg hover:bg-[#162d4a] transition-all duration-200 active:scale-95"
        @click="scrollToTop"
      >
        <i class="pi pi-arrow-up text-sm" />
      </button>
    </Transition>
  </div>
</template>

<style scoped>
.menu-item-lateral.activo {
  background-color: #d2d7e4 !important;
  font-weight: 600;
  color: #1e3a5f;
}
aside .menu-item-lateral.activo {
  background-color: #d2d7e4 !important;
  color: #1e3a5f;
  font-weight: 600;
}
</style>
