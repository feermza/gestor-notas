<script setup>
/**
 * NotasView — Vista unificada con query params.
 * Lee estado, atrasadas, sin_asignar al montar y preactiva filtros.
 * Título dinámico según filtro activo.
 * Botón "Nueva Nota" visible para ADMINISTRADOR, SUPERVISOR, OPERADOR (no CONSULTOR).
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { get } from '@/api/cliente'
import { useAuthStore } from '@/stores/auth'
import TablaNotas from '@/components/TablaNotas.vue'
import {
  LABELS_ESTADO,
  LABELS_PRIORIDAD,
} from '@/utils/notas'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

// Estado de carga y error
const cargando = ref(true)
const error = ref(null)
const notas = ref([])

// Filtros (aplicados en frontend)
const textoBusqueda = ref('')
const filtroEstado = ref(null)
const filtroPrioridad = ref(null)
const soloAtrasadas = ref(false)
const sinAsignar = ref(false)

const paginaActual = ref(1)
const porPagina = ref(10)

// Botón "Nueva Nota": visible para ADMINISTRADOR, SUPERVISOR, OPERADOR
const puedeCrearNota = computed(() =>
  ['ADMINISTRADOR', 'SUPERVISOR', 'OPERADOR'].includes(auth.usuario?.rol),
)

// Opciones para dropdowns (estados y prioridades)
const opcionesEstado = computed(() => {
  return Object.entries(LABELS_ESTADO).map(([value, label]) => ({ value, label }))
})
const opcionesPrioridad = computed(() => {
  return Object.entries(LABELS_PRIORIDAD).map(([value, label]) => ({ value, label }))
})

// Notas filtradas
const notasFiltradas = computed(() => {
  let lista = notas.value

  // Búsqueda por texto (número, tema, remitente)
  const texto = (textoBusqueda.value || '').trim().toLowerCase()
  if (texto) {
    lista = lista.filter(
      (n) =>
        (n.numero_nota || '').toLowerCase().includes(texto) ||
        (n.numero_nota_interno || '').toLowerCase().includes(texto) ||
        (n.tema || '').toLowerCase().includes(texto) ||
        (n.remitente || '').toLowerCase().includes(texto),
    )
  }

  if (filtroEstado.value) {
    lista = lista.filter((n) => n.estado === filtroEstado.value)
  }
  if (filtroPrioridad.value) {
    lista = lista.filter((n) => n.prioridad === filtroPrioridad.value)
  }
  if (soloAtrasadas.value) {
    lista = lista.filter((n) => n.atrasada)
  }
  // Sin asignar: solo notas sin responsable
  if (sinAsignar.value) {
    lista = lista.filter((n) => !n.responsable || !n.responsable.id)
  }

  return lista
})

const notasPaginadas = computed(() => {
  const inicio = (paginaActual.value - 1) * porPagina.value
  return notasFiltradas.value.slice(inicio, inicio + porPagina.value)
})

const totalPaginas = computed(() =>
  Math.max(1, Math.ceil(notasFiltradas.value.length / porPagina.value)),
)

// Contador total
const totalNotas = computed(() => notasFiltradas.value.length)

// Título dinámico según filtro activo
const tituloVista = computed(() => {
  const n = totalNotas.value
  if (sinAsignar.value) return `Sin Asignar (${n})`
  if (soloAtrasadas.value) return `Notas Atrasadas (${n})`
  if (filtroEstado.value === 'INGRESADA') return `Notas Ingresadas (${n})`
  if (filtroEstado.value === 'EN_PROCESO') return `Notas en Proceso (${n})`
  if (filtroEstado.value === 'EN_ESPERA') return `Notas en Espera (${n})`
  if (filtroEstado.value === 'RESUELTA') return `Notas Resueltas (${n})`
  return `Notas (${n})`
})

function limpiarFiltros() {
  textoBusqueda.value = ''
  filtroEstado.value = null
  filtroPrioridad.value = null
  soloAtrasadas.value = false
  sinAsignar.value = false
}

async function cargarNotas() {
  cargando.value = true
  error.value = null
  try {
    const res = await get('/api/notas/')
    notas.value = Array.isArray(res) ? res : res.results || []
  } catch (e) {
    error.value = e.data?.detalle || e.data?.error || e.message || 'Error al cargar las notas.'
  } finally {
    cargando.value = false
  }
}

// Aplicar query params a los filtros (para navegación programática)
function aplicarQueryParams() {
  const q = route.query
  // Resetear siempre primero (null para que el Dropdown muestre placeholder cuando no hay valor)
  filtroEstado.value = null
  filtroPrioridad.value = null
  soloAtrasadas.value = false
  sinAsignar.value = false
  textoBusqueda.value = ''
  // Luego activar los que correspondan (value = string igual a option-value, ej. 'EN_PROCESO')
  if (q.estado) filtroEstado.value = q.estado
  if (q.prioridad) filtroPrioridad.value = q.prioridad
  if (q.atrasadas === 'true') soloAtrasadas.value = true
  if (q.sin_asignar === 'true') sinAsignar.value = true
  if (q.search) textoBusqueda.value = q.search
}

function irANueva() {
  router.push('/notas/nueva')
}

onMounted(() => {
  // Preactivar buscador si se llegó con ?search= (p. ej. desde búsqueda global del navbar)
  const searchQuery = route.query.search
  if (searchQuery) textoBusqueda.value = searchQuery
  aplicarQueryParams()
  cargarNotas()
})

// Si cambian los query params (ej. navegación desde dashboard), reaplicar filtros y actualizar tabla
watch(
  () => route.query,
  () => {
    aplicarQueryParams()
    cargarNotas()
  },
  { deep: true },
)

watch(
  () => [
    textoBusqueda.value,
    filtroEstado.value,
    filtroPrioridad.value,
    soloAtrasadas.value,
    sinAsignar.value,
  ],
  () => {
    paginaActual.value = 1
  },
)

watch(totalPaginas, (tp) => {
  if (paginaActual.value > tp) paginaActual.value = tp
})
</script>

<template>
  <div class="notas-view min-h-full" style="background-color: #eef2f7">
    <div class="p-4 md:p-6">
      <!-- Título dinámico con contador -->
      <header class="mb-6">
        <h1 class="text-2xl md:text-3xl font-bold text-[#1e3a5f]">{{ tituloVista }}</h1>
      </header>

      <!-- Mensaje de error -->
      <div
        v-if="error"
        class="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm flex flex-wrap items-center gap-2"
      >
        <span class="flex-1">{{ error }}</span>
        <Button label="Reintentar" icon="pi pi-refresh" size="small" @click="cargarNotas" />
      </div>

      <!-- Barra de herramientas -->
      <div class="mb-4 flex flex-col sm:flex-row flex-wrap gap-3 items-stretch sm:items-center">
        <Button
          v-if="puedeCrearNota"
          label="Nueva Nota"
          icon="pi pi-plus"
          @click="irANueva"
          style="
            background-color: #1e3a5f !important;
            border-color: #1e3a5f !important;
            color: white !important;
            font-weight: 600;
          "
        />
        <div class="relative flex-1 min-w-[200px] max-w-md">
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 z-10" />
          <input
            v-model="textoBusqueda"
            type="text"
            placeholder="Buscar por número, tema o remitente"
            class="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg bg-white text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#2d6a9f] focus:border-transparent"
          />
        </div>
        <Dropdown
          v-model="filtroEstado"
          :options="opcionesEstado"
          option-label="label"
          option-value="value"
          placeholder="Estado"
          show-clear
          class="w-full sm:w-[180px]"
        />
        <Dropdown
          v-model="filtroPrioridad"
          :options="opcionesPrioridad"
          option-label="label"
          option-value="value"
          placeholder="Prioridad"
          show-clear
          class="w-full sm:w-[180px]"
        />
        <button
          type="button"
          @click="limpiarFiltros"
          class="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-gray-600 bg-white hover:bg-gray-50 transition-colors text-sm font-medium"
        >
          <i class="pi pi-filter-slash" />
          Limpiar filtros
        </button>
      </div>

      <!-- ProgressBar mientras carga -->
      <div v-if="cargando" class="mb-4">
        <ProgressBar mode="indeterminate" style="height: 4px" />
      </div>

      <TablaNotas :notas="notasPaginadas" :cargando="cargando" desde="notas" />

      <div
        v-if="!cargando"
        class="pie-paginacion flex items-center justify-between px-4 py-3 border border-gray-100 border-t-0 bg-white rounded-b-xl shadow-sm"
      >
        <span class="text-xs text-gray-600"> {{ notasFiltradas.length }} notas </span>
        <div class="flex items-center gap-2">
          <button
            type="button"
            @click="paginaActual--"
            :disabled="paginaActual === 1"
            class="px-2 py-1 rounded text-sm text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ‹
          </button>
          <span class="text-xs text-gray-500">
            {{ paginaActual }} / {{ totalPaginas }}
          </span>
          <button
            type="button"
            @click="paginaActual++"
            :disabled="paginaActual === totalPaginas"
            class="px-2 py-1 rounded text-sm text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ›
          </button>
        </div>
      </div>

      <div v-if="!cargando" class="mt-3 flex justify-end">
        <button
          type="button"
          @click="cargarNotas"
          class="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 text-[#1e3a5f] bg-white transition-colors text-sm font-medium shadow-sm hover:bg-[#475569] hover:text-white hover:border-[#475569]"
        >
          <i class="pi pi-refresh" />
          Recargar
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notas-view {
  min-height: 100%;
}
</style>
