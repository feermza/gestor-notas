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
} from '@/utils/notas'

const router = useRouter()

const cargando = ref(true)
const error = ref(null)
const notas = ref([])

const textoBusqueda = ref('')

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

const totalPendientes = computed(() => pendientesFiltrados.value.length)

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

function irADetalle(id) {
  router.push(`/notas/${id}`)
}

function claseFila(nota) {
  const atrasada = nota.atrasada ?? esAtrasada(nota)
  return atrasada ? 'fila-atrasada' : ''
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

      <div v-if="!cargando" class="card rounded-xl overflow-hidden shadow-md">
        <DataTable
          :value="pendientesFiltrados"
          :row-class="claseFila"
          paginator
          :rows="10"
          :rows-per-page-options="[10, 25, 50]"
          data-key="id"
          striped-rows
          responsive-layout="stack"
          breakpoint="960px"
          class="p-datatable-sm"
          current-page-report-template="Mostrando {first} a {last} de {totalRecords} pendientes"
        >
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

          <Column field="tema" header="Tema">
            <template #body="{ data }">
              <span v-tooltip.top="data.tema || '—'" class="block truncate max-w-[200px]">
                {{ truncar(data.tema, 50) || '—' }}
              </span>
            </template>
          </Column>

          <Column field="tarea_asignada" header="Tarea asignada">
            <template #body="{ data }">
              <span v-tooltip.top="data.tarea_asignada || '—'" class="block truncate max-w-[240px]">
                {{ truncar(data.tarea_asignada, 50) || '—' }}
              </span>
            </template>
          </Column>

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

          <Column field="fecha_ingreso" header="Fecha ingreso">
            <template #body="{ data }">
              {{ formatoFecha(data.fecha_ingreso) }}
            </template>
          </Column>

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

          <template #empty>
            <div class="py-12 text-center text-gray-500">
              <i class="pi pi-inbox-in text-4xl mb-3 block opacity-60" />
              <p class="text-base font-medium">No tenés notas pendientes. ¡Todo al día!</p>
            </div>
          </template>
        </DataTable>

        <div class="p-3 border-t border-gray-100 flex justify-end">
          <button
            type="button"
            @click="cargarPendientes"
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
.pendientes-view {
  min-height: 100%;
}
</style>
