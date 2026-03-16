<script setup>
/**
 * MiTrabajoView — Vista para OPERADOR con sus notas pendientes.
 * Ruta: /mi-trabajo
 * Tabs: Todas | Para iniciar (ASIGNADA) | En proceso | En espera
 * Cards simples (no DataTable), ordenadas por prioridad.
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { get } from '@/api/cliente'
import {
  colorEstado,
  labelEstado,
  haceCuanto,
} from '@/utils/notas'

const router = useRouter()
const route = useRoute()

// Estado
const cargando = ref(true)
const error = ref(null)
const notas = ref([])

// Tab activo: 'todas' | 'ASIGNADA' | 'EN_PROCESO' | 'EN_ESPERA'
const tabActivo = ref('todas')

// Buscador simple
const textoBusqueda = ref('')

// Ordenar por prioridad: URGENTE, ALTA, NORMAL, BAJA
const ordenPrioridad = { URGENTE: 0, ALTA: 1, NORMAL: 2, MEDIA: 2, BAJA: 3 }
function ordenarPorPrioridad(lista) {
  return [...lista].sort((a, b) => {
    const pa = ordenPrioridad[a.prioridad] ?? 4
    const pb = ordenPrioridad[b.prioridad] ?? 4
    return pa - pb
  })
}

// Notas filtradas por tab y búsqueda
const notasFiltradas = computed(() => {
  let lista = notas.value

  // Filtro por tab
  if (tabActivo.value !== 'todas') {
    lista = lista.filter((n) => n.estado === tabActivo.value)
  }

  // Búsqueda por número o tema
  const texto = (textoBusqueda.value || '').trim().toLowerCase()
  if (texto) {
    lista = lista.filter(
      (n) =>
        (n.numero_nota || '').toLowerCase().includes(texto) ||
        (n.numero_nota_interno || '').toLowerCase().includes(texto) ||
        (n.tema || '').toLowerCase().includes(texto),
    )
  }

  return ordenarPorPrioridad(lista)
})

// Contador total
const totalNotas = computed(() => notasFiltradas.value.length)

async function cargarPendientes() {
  cargando.value = true
  error.value = null
  try {
    const res = await get('/api/notas/pendientes/')
    notas.value = Array.isArray(res) ? res : res.results || []
  } catch (e) {
    error.value = e.data?.detalle || e.data?.error || e.message || 'Error al cargar las notas.'
    notas.value = []
  } finally {
    cargando.value = false
  }
}

// Preactivar tab según query param ?estado
onMounted(() => {
  const estadoQuery = route.query.estado
  if (estadoQuery && ['ASIGNADA', 'EN_PROCESO', 'EN_ESPERA'].includes(estadoQuery)) {
    tabActivo.value = estadoQuery
  }
  cargarPendientes()
})
</script>

<template>
  <div class="mi-trabajo min-h-full" style="background-color: #eef2f7">
    <div class="p-4 md:p-6">
      <!-- Título con contador -->
      <header class="mb-6">
        <h1 class="text-2xl md:text-3xl font-bold text-[#1e3a5f]">Mi Trabajo ({{ totalNotas }})</h1>
      </header>

      <!-- Error -->
      <div
        v-if="error"
        class="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm flex items-center justify-between gap-2"
      >
        <span>{{ error }}</span>
        <Button label="Reintentar" icon="pi pi-refresh" size="small" @click="cargarPendientes" />
      </div>

      <!-- Buscador simple -->
      <div class="mb-4">
        <div class="relative max-w-md">
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            v-model="textoBusqueda"
            type="text"
            placeholder="Buscar por número o tema"
            class="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg bg-white text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#2d6a9f] focus:border-transparent"
          />
        </div>
      </div>

      <!-- Tabs (botones toggle) -->
      <div class="flex flex-wrap gap-2 mb-6">
        <button
          type="button"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="
            tabActivo === 'todas'
              ? 'bg-[#1e3a5f] text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          "
          @click="tabActivo = 'todas'"
        >
          Todas
        </button>
        <button
          type="button"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="
            tabActivo === 'ASIGNADA'
              ? 'bg-[#1e3a5f] text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          "
          @click="tabActivo = 'ASIGNADA'"
        >
          Para iniciar
        </button>
        <button
          type="button"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="
            tabActivo === 'EN_PROCESO'
              ? 'bg-[#1e3a5f] text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          "
          @click="tabActivo = 'EN_PROCESO'"
        >
          En proceso
        </button>
        <button
          type="button"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="
            tabActivo === 'EN_ESPERA'
              ? 'bg-[#1e3a5f] text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          "
          @click="tabActivo = 'EN_ESPERA'"
        >
          En espera
        </button>
      </div>

      <!-- Loading -->
      <div v-if="cargando" class="flex justify-center py-12">
        <ProgressBar mode="indeterminate" style="height: 4px; width: 100%; max-width: 400px" />
      </div>

      <!-- Lista de notas (cards) -->
      <div v-else class="space-y-4">
        <template v-if="notasFiltradas.length === 0">
          <div class="py-12 text-center text-gray-500 bg-white rounded-lg shadow-sm">
            <i class="pi pi-inbox text-4xl mb-2 block opacity-60" />
            <p>No hay notas en esta categoría.</p>
          </div>
        </template>
        <div
          v-for="nota in notasFiltradas"
          :key="nota.id"
          class="bg-white rounded-lg p-4 shadow-sm border-l-4"
          :style="{ borderLeftColor: colorEstado(nota.estado) }"
        >
          <div class="flex justify-between items-start">
            <div>
              <p class="font-mono text-sm text-[#1e3a5f] font-bold">
                {{ nota.numero_nota || nota.numero_nota_interno || '—' }}
              </p>
              <p class="font-semibold text-gray-800 mt-1">{{ nota.tema || '—' }}</p>
              <p class="text-sm text-gray-500 mt-1 flex items-center gap-1">
                <i class="pi pi-flag text-xs" />
                {{ nota.tarea_asignada || 'Sin tarea asignada' }}
              </p>
            </div>
            <div class="flex flex-col items-end gap-2">
              <span
                class="px-2 py-1 rounded-full text-xs text-white font-medium"
                :style="{ backgroundColor: colorEstado(nota.estado) }"
              >
                {{ labelEstado(nota.estado) }}
              </span>
              <span class="text-xs text-gray-400">{{ haceCuanto(nota.fecha_ingreso) }}</span>
            </div>
          </div>
          <div class="mt-3 flex justify-end">
            <button
              type="button"
              class="text-sm text-[#1e3a5f] hover:underline font-medium"
              @click="router.push(`/notas/${nota.id}?desde=mi-trabajo`)"
            >
              Ver detalle →
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mi-trabajo {
  min-height: 100%;
}
</style>
