<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { get } from '@/api/cliente'
import BtnDetalle from '@/components/BtnDetalle.vue'
import {
  COLORES_ESTADO,
  COLORES_PRIORIDAD,
  LABELS_ESTADO,
  truncar,
  haceCuanto,
  esAtrasada,
} from '@/utils/notas'

const cargando = ref(true)
const error = ref(null)
const notas = ref([])

const textoBusqueda = ref('')
const hoverId = ref(null)
const paginaActual = ref(1)
const porPagina = ref(10)

const pendientesFiltrados = computed(() => {
  let lista = notas.value
  const texto = (textoBusqueda.value || '').trim().toLowerCase()
  if (texto) {
    lista = lista.filter(
      (n) =>
        (n.numero_nota || '').toLowerCase().includes(texto) ||
        (n.tema || '').toLowerCase().includes(texto),
    )
  }
  return lista
})

const notasPaginadas = computed(() => {
  const inicio = (paginaActual.value - 1) * porPagina.value
  return pendientesFiltrados.value.slice(inicio, inicio + porPagina.value)
})

const totalPaginas = computed(() =>
  Math.max(1, Math.ceil(pendientesFiltrados.value.length / porPagina.value)),
)

const totalPendientes = computed(() => pendientesFiltrados.value.length)

watch(textoBusqueda, () => {
  paginaActual.value = 1
})

watch(totalPaginas, (tp) => {
  if (paginaActual.value > tp) paginaActual.value = tp
})

async function cargarPendientes() {
  cargando.value = true
  error.value = null
  try {
    const res = await get('/api/notas/pendientes/')
    notas.value = Array.isArray(res) ? res : res.results || []
  } catch (e) {
    error.value = e.data?.detalle || e.data?.error || e.message || 'Error al cargar los pendientes.'
  } finally {
    cargando.value = false
  }
}

onMounted(cargarPendientes)
</script>

<template>
  <div class="pendientes-view min-h-full" style="background-color: #eef2f7">
    <div class="p-4 md:p-6">
      <header class="mb-6">
        <h1 class="text-2xl md:text-3xl font-bold text-[#1e3a5f]">
          Mis Pendientes ({{ totalPendientes }})
        </h1>
      </header>

      <div
        v-if="error"
        class="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm flex flex-wrap items-center gap-2"
      >
        <span class="flex-1">{{ error }}</span>
        <Button label="Reintentar" icon="pi pi-refresh" size="small" @click="cargarPendientes" />
      </div>

      <div class="mb-4 flex flex-col sm:flex-row flex-wrap gap-3 items-stretch sm:items-center">
        <div class="relative flex-1 min-w-[200px] max-w-md">
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 z-10" />
          <input
            v-model="textoBusqueda"
            type="text"
            placeholder="Buscar por número o tema"
            class="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg bg-white text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#2d6a9f] focus:border-transparent"
          />
        </div>
      </div>

      <div v-if="cargando" class="mb-4">
        <ProgressBar mode="indeterminate" style="height: 4px" />
      </div>

      <div
        v-if="!cargando"
        class="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100"
      >
        <template v-if="pendientesFiltrados.length === 0">
          <div class="py-12 text-center text-gray-500">
            <i class="pi pi-inbox text-4xl mb-3 block opacity-60" />
            <p class="text-base font-medium">No tenés notas pendientes. ¡Todo al día!</p>
          </div>
        </template>
        <template v-else>
          <div class="notas-header">
            <span>Número</span>
            <span>Tema</span>
            <span>Tarea</span>
            <span>Estado</span>
            <span>Prioridad</span>
            <span>Ingreso</span>
            <span></span>
          </div>
          <ul class="divide-y divide-gray-100">
            <li
              v-for="nota in notasPaginadas"
              :key="nota.id"
              class="fila-nota"
              :class="{
                'fila-nota--atrasada': nota.atrasada ?? esAtrasada(nota),
              }"
              @mouseenter="hoverId = nota.id"
              @mouseleave="hoverId = null"
              :style="{
                display: 'grid',
                gridTemplateColumns: '130px 1fr 120px 110px 90px 90px 110px',
                alignItems: 'center',
                gap: '12px',
                borderLeftColor:
                  hoverId === nota.id ? COLORES_ESTADO[nota.estado] : 'transparent',
              }"
            >
              <span class="font-mono text-sm font-bold text-[#1e3a5f] min-w-0">
                {{ nota.numero_nota || nota.numero_nota_interno || '—' }}
              </span>
              <span v-tooltip.top="nota.tema || '—'" class="text-sm text-gray-800 truncate min-w-0">
                {{ truncar(nota.tema, 48) || '—' }}
              </span>
              <span
                v-tooltip.top="nota.tarea_asignada || '—'"
                class="text-xs text-gray-600 truncate min-w-0"
              >
                {{ truncar(nota.tarea_asignada, 28) || '—' }}
              </span>
              <span
                class="px-2 py-0.5 rounded-full text-xs text-white font-medium text-center min-w-0 justify-self-center"
                :style="{ backgroundColor: COLORES_ESTADO[nota.estado] }"
              >
                {{ LABELS_ESTADO[nota.estado] }}
              </span>
              <span
                class="px-2 py-0.5 rounded-full text-xs font-medium text-center min-w-0 justify-self-center"
                :class="{
                  'text-white': !['NORMAL', 'MEDIA'].includes(nota.prioridad),
                  'text-slate-800': ['NORMAL', 'MEDIA'].includes(nota.prioridad),
                  'tag-urgente': nota.prioridad === 'URGENTE',
                }"
                :style="{ backgroundColor: COLORES_PRIORIDAD[nota.prioridad] || '#64748b' }"
              >
                {{ nota.prioridad }}
              </span>
              <span class="text-xs text-gray-600 text-right min-w-0">
                {{ haceCuanto(nota.fecha_ingreso) }}
              </span>
              <span class="justify-self-end min-w-0">
                <BtnDetalle :nota-id="nota.id" desde="pendientes" />
              </span>
            </li>
          </ul>
          <div class="pie-paginacion flex items-center justify-between px-4 py-3 border-t border-gray-100 bg-white">
            <span class="text-xs text-gray-600"> {{ pendientesFiltrados.length }} pendientes </span>
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
        </template>
      </div>

      <div v-if="!cargando" class="mt-3 flex justify-end">
        <button
          type="button"
          @click="cargarPendientes"
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
.pendientes-view {
  min-height: 100%;
}

.notas-header {
  display: grid;
  grid-template-columns: 130px 1fr 120px 110px 90px 90px 110px;
  align-items: center;
  padding: 10px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  gap: 12px;
}

.fila-nota {
  padding: 10px 16px;
  background: white;
  border-left: 3px solid transparent;
  transition: all 0.15s;
  cursor: default;
}

.fila-nota:hover {
  background: #d2d7e4;
}

.fila-nota--atrasada {
  background: #fff5f5;
}

.fila-nota--atrasada:hover {
  background: #d2d7e4;
}
</style>
