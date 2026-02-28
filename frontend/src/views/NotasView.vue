<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get } from '@/api/cliente'
import {
  truncar,
  formatoFecha,
  colorEstado,
  labelEstado,
  colorPrioridad,
  labelPrioridad,
  esAtrasada,
  LABELS_ESTADO,
  LABELS_PRIORIDAD,
} from '@/utils/notas'

const router = useRouter()

// Estado de carga y error
const cargando = ref(true)
const error = ref(null)
const notas = ref([])

// Filtros (aplicados en frontend)
const textoBusqueda = ref('')
const filtroEstado = ref(null)
const filtroPrioridad = ref(null)

// Opciones para dropdowns (estados y prioridades)
const opcionesEstado = computed(() => {
  return Object.entries(LABELS_ESTADO).map(([value, label]) => ({ value, label }))
})
const opcionesPrioridad = computed(() => {
  return Object.entries(LABELS_PRIORIDAD).map(([value, label]) => ({ value, label }))
})

// Notas filtradas (búsqueda por numero_nota_interno, tema, remitente)
const notasFiltradas = computed(() => {
  let lista = notas.value

  // Búsqueda por texto
  const texto = (textoBusqueda.value || '').trim().toLowerCase()
  if (texto) {
    lista = lista.filter(
      (n) =>
        (n.numero_nota || '').toLowerCase().includes(texto) ||
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

  return lista
})

// Contador total para el título
const totalNotas = computed(() => notasFiltradas.value.length)

function limpiarFiltros() {
  textoBusqueda.value = ''
  filtroEstado.value = null
  filtroPrioridad.value = null
}

async function cargarNotas() {
  cargando.value = true
  error.value = null
  try {
    const res = await get('/api/notas/')
    // La API puede devolver array o objeto paginado { results: [...] }
    notas.value = Array.isArray(res) ? res : res.results || []
  } catch (e) {
    error.value = e.data?.detalle || e.data?.error || e.message || 'Error al cargar las notas.'
  } finally {
    cargando.value = false
  }
}

function irADetalle(id) {
  router.push(`/notas/${id}`)
}

function irANueva() {
  router.push('/notas/nueva')
}

// Nombre del responsable o "Sin asignar"
function nombreResponsable(nota) {
  return nota.responsable || 'Sin asignar'
}

// Clase de fila: fondo rojizo si está atrasada
function claseFila(nota) {
  const atrasada = nota.atrasada ?? esAtrasada(nota)
  return atrasada ? 'fila-atrasada' : ''
}

onMounted(cargarNotas)
</script>

<template>
  <div class="notas-view min-h-full" style="background-color: #eef2f7">
    <div class="p-4 md:p-6">
      <!-- Título con contador -->
      <header class="mb-6">
        <h1 class="text-2xl md:text-3xl font-bold text-[#1e3a5f]">Notas ({{ totalNotas }})</h1>
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

      <!-- Tabla de notas (solo cuando no está cargando) -->
      <div v-if="!cargando" class="card rounded-xl overflow-hidden shadow-md">
        <DataTable
          :value="notasFiltradas"
          :row-class="claseFila"
          paginator
          :rows="10"
          :rows-per-page-options="[10, 25, 50]"
          data-key="id"
          striped-rows
          responsive-layout="stack"
          breakpoint="960px"
          class="p-datatable-sm"
          current-page-report-template="Mostrando {first} a {last} de {totalRecords} notas"
        >
          <!-- Columna Número (clickeable) -->
          <Column field="numero_nota" header="Número" sortable>
            <template #body="{ data }">
              <button
                type="button"
                class="font-mono text-sm text-[#1e3a5f] hover:underline cursor-pointer bg-transparent border-none p-0"
                @click="irADetalle(data.id)"
              >
                {{ data.numero_nota || '—' }}
              </button>
            </template>
          </Column>

          <!-- Columna Tema (truncado 50 chars + tooltip) -->
          <Column field="tema" header="Tema">
            <template #body="{ data }">
              <span v-tooltip.top="data.tema || '—'" class="block truncate max-w-[200px]">
                {{ truncar(data.tema, 50) || '—' }}
              </span>
            </template>
          </Column>

          <!-- Columna Remitente -->
          <Column field="remitente" header="Remitente">
            <template #body="{ data }">
              {{ data.remitente || '—' }}
            </template>
          </Column>

          <!-- Columna Estado (Tag con color) -->
          <Column field="estado" header="Estado">
            <template #body="{ data }">
              <Tag
                :value="labelEstado(data.estado)"
                :style="{
                  background: colorEstado(data.estado),
                  color: 'white',
                  border: 'none',
                }"
                class="!text-xs"
              />
            </template>
          </Column>

          <!-- Columna Prioridad (COLORES_PRIORIDAD; URGENTE con pulso) -->
          <Column field="prioridad" header="Prioridad">
            <template #body="{ data }">
              <Tag
                :value="labelPrioridad(data.prioridad)"
                :class="{ 'tag-urgente': data.prioridad === 'URGENTE' }"
                :style="{
                  background: colorPrioridad(data.prioridad),
                  color: ['BAJA', 'NORMAL', 'MEDIA'].includes(data.prioridad) ? '#1e293b' : 'white',
                  border: 'none',
                }"
                class="!text-xs"
              />
            </template>
          </Column>

          <!-- Columna Responsable -->
          <Column header="Responsable">
            <template #body="{ data }">
              <span :class="data.responsable ? 'text-gray-800' : 'text-gray-400'">
                {{ nombreResponsable(data) }}
              </span>
            </template>
          </Column>

          <!-- Columna Fecha límite (en rojo si atrasada) -->
          <Column field="fecha_limite" header="Fecha límite">
            <template #body="{ data }">
              <span
                :class="
                  (data.atrasada ?? esAtrasada(data)) ? 'text-red-600 font-medium' : 'text-gray-700'
                "
              >
                {{ formatoFecha(data.fecha_limite) }}
              </span>
            </template>
          </Column>

          <!-- Columna Acciones (botón ojo) -->
          <Column header="Acciones" class="acciones-col">
            <template #body="{ data }">
              <Button
                icon="pi pi-eye"
                text
                rounded
                severity="secondary"
                size="small"
                v-tooltip.top="'Ver detalle'"
                @click="irADetalle(data.id)"
              />
            </template>
          </Column>

          <!-- Template vacío cuando no hay datos -->
          <template #empty>
            <div class="py-8 text-center text-gray-500">
              <i class="pi pi-inbox text-4xl mb-2 block opacity-60" />
              <p>{{ error ? 'Error al cargar. Usá "Reintentar".' : 'No hay notas.' }}</p>
            </div>
          </template>
        </DataTable>

        <!-- Botón recarga manual -->
        <div class="p-3 border-t border-gray-100 flex justify-end">
          <button
            type="button"
            @click="cargarNotas"
            class="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 text-[#1e3a5f] bg-white hover:bg-[#eef2f7] transition-colors text-sm font-medium shadow-sm"
          >
            <i class="pi pi-refresh" />
            Recargar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notas-view {
  min-height: 100%;
}

.notas-view :deep(.p-button-label) {
  color: white !important;
}

.notas-view :deep(.p-datatable) {
  background-color: white !important;
}
.notas-view :deep(.p-datatable-table) {
  background-color: white !important;
}
.notas-view :deep(.p-datatable-thead > tr > th) {
  background-color: #f8fafc !important;
  color: #1e293b !important;
  border-bottom: 2px solid #e2e8f0 !important;
}
.notas-view :deep(.p-datatable-tbody > tr) {
  background-color: white !important;
  color: #1e293b !important;
}
.notas-view :deep(.p-datatable-tbody > tr:hover) {
  background-color: #f1f5f9 !important;
}
.notas-view :deep(.p-datatable-tbody > tr.fila-atrasada) {
  background-color: #fff5f5 !important;
}
.notas-view :deep(.p-paginator) {
  background-color: white !important;
  color: #1e293b !important;
  border-top: 1px solid #e2e8f0 !important;
}
.notas-view :deep(.p-select),
.notas-view :deep(.p-select-overlay) {
  background-color: white !important;
  color: #1e293b !important;
  border: 1px solid #e2e8f0 !important;
}
.notas-view :deep(.p-select-option) {
  color: #1e293b !important;
}
.notas-view :deep(.p-select-option:hover) {
  background-color: #f1f5f9 !important;
}

@keyframes pulso {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}
.tag-urgente {
  animation: pulso 1.5s ease-in-out infinite;
}

/* Responsive: en móvil la tabla usa layout apilado */
.notas-view :deep(.p-datatable .p-datatable-tbody > tr > td) {
  word-break: break-word;
}
</style>
