<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get } from '@/api/cliente'

const router = useRouter()

// Estado del dashboard
const cargando = ref(true)
const error = ref(null)

// Datos de las tarjetas superiores
const ingresadasHoy = ref(0)
const enProceso = ref(0)
const atrasadas = ref(0)
const resueltasEsteMes = ref(0)

// Listas de los paneles inferiores
const pendientes = ref([])
const ultimasIngresadas = ref([])

// Fecha actual formateada para el título
const fechaActual = computed(() => {
  const ahora = new Date()
  const dias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
  const meses = [
    'enero',
    'febrero',
    'marzo',
    'abril',
    'mayo',
    'junio',
    'julio',
    'agosto',
    'septiembre',
    'octubre',
    'noviembre',
    'diciembre',
  ]
  const dia = dias[ahora.getDay()]
  const numero = ahora.getDate()
  const mes = meses[ahora.getMonth()]
  const anio = ahora.getFullYear()
  return `${dia}, ${numero} de ${mes} de ${anio}`
})

// Colores de estado para Tags (según especificación)
const COLORES_ESTADO = {
  INGRESADA: '#64748b',
  EN_REVISION: '#2d6a9f',
  ASIGNADA: '#f59e0b',
  EN_PROCESO: '#1e3a5f',
  EN_ESPERA: '#d97706',
  DEVUELTA: '#ef4444',
  RESUELTA: '#27ae60',
  ARCHIVADA: '#94a3b8',
  ANULADA: '#991b1b',
}

const LABELS_ESTADO = {
  INGRESADA: 'Ingresada',
  EN_REVISION: 'En Revisión',
  ASIGNADA: 'Asignada',
  EN_PROCESO: 'En Proceso',
  EN_ESPERA: 'En Espera',
  DEVUELTA: 'Devuelta',
  RESUELTA: 'Resuelta',
  ARCHIVADA: 'Archivada',
  ANULADA: 'Anulada',
}

function truncar(texto, max = 40) {
  if (!texto) return ''
  return texto.length <= max ? texto : texto.slice(0, max) + '…'
}

function formatoFecha(fechaStr) {
  if (!fechaStr) return '—'
  const d = new Date(fechaStr + 'T12:00:00')
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

/** "hace X minutos", "hace 2 horas", "ayer", "hace 3 días" */
function haceCuanto(fechaStr) {
  if (!fechaStr) return '—'
  const fecha = new Date(fechaStr + 'T12:00:00')
  const ahora = new Date()
  const diffMs = ahora - fecha
  const diffDias = Math.floor(diffMs / (24 * 60 * 60 * 1000))
  const diffHoras = Math.floor(diffMs / (60 * 60 * 1000))
  const diffMin = Math.floor(diffMs / (60 * 1000))

  if (diffMin < 60) return diffMin <= 1 ? 'hace un momento' : `hace ${diffMin} minutos`
  if (diffHoras < 24) return diffHoras === 1 ? 'hace 1 hora' : `hace ${diffHoras} horas`
  if (diffDias === 1) return 'ayer'
  if (diffDias < 7) return `hace ${diffDias} días`
  return formatoFecha(fechaStr)
}

function colorEstado(estado) {
  return COLORES_ESTADO[estado] || '#64748b'
}

function labelEstado(estado) {
  return LABELS_ESTADO[estado] || estado || '—'
}

/** Devuelve true si fecha_ingreso está en el mes actual */
function esDelMesActual(fechaStr) {
  if (!fechaStr) return false
  const d = new Date(fechaStr + 'T12:00:00')
  const hoy = new Date()
  return d.getFullYear() === hoy.getFullYear() && d.getMonth() === hoy.getMonth()
}

/** Devuelve true si fecha_ingreso es hoy */
function esHoy(fechaStr) {
  if (!fechaStr) return false
  const d = new Date(fechaStr + 'T12:00:00')
  const hoy = new Date()
  return (
    d.getFullYear() === hoy.getFullYear() &&
    d.getMonth() === hoy.getMonth() &&
    d.getDate() === hoy.getDate()
  )
}

async function cargarDashboard() {
  cargando.value = true
  error.value = null
  try {
    const [rEnProceso, rAtrasadas, rPendientes, rLista, rResueltas, rArchivadas] =
      await Promise.all([
        get('/api/notas/?estado=EN_PROCESO'),
        get('/api/notas/atrasadas/'),
        get('/api/notas/pendientes/'),
        get('/api/notas/'),
        get('/api/notas/?estado=RESUELTA'),
        get('/api/notas/?estado=ARCHIVADA'),
      ])

    // En proceso: respuesta paginada
    const listaEnProceso = Array.isArray(rEnProceso) ? rEnProceso : rEnProceso.results || []
    enProceso.value = Array.isArray(rEnProceso)
      ? rEnProceso.length
      : (rEnProceso.count ?? listaEnProceso.length)

    // Atrasadas: array
    atrasadas.value = Array.isArray(rAtrasadas) ? rAtrasadas.length : 0

    // Pendientes: array, máximo 5 para el panel
    pendientes.value = Array.isArray(rPendientes) ? rPendientes.slice(0, 5) : []

    // Lista principal: para ingresadas hoy y últimas 5
    const listaGeneral = Array.isArray(rLista) ? rLista : rLista.results || []
    ingresadasHoy.value = listaGeneral.filter((n) => esHoy(n.fecha_ingreso)).length
    ultimasIngresadas.value = listaGeneral.slice(0, 5)

    // Resueltas/archivadas este mes (combinar ambas listas y filtrar por mes)
    const listasResueltas = [
      ...(Array.isArray(rResueltas) ? rResueltas : rResueltas.results || []),
      ...(Array.isArray(rArchivadas) ? rArchivadas : rArchivadas.results || []),
    ]
    resueltasEsteMes.value = listasResueltas.filter((n) => esDelMesActual(n.fecha_ingreso)).length
  } catch (e) {
    error.value = e.data?.detalle || e.message || 'Error al cargar el panel de control.'
  } finally {
    cargando.value = false
  }
}

function irA(ruta) {
  router.push(ruta)
}

onMounted(cargarDashboard)
</script>

<template>
  <div class="dashboard min-h-full" style="background-color: #f8fafc">
    <div class="p-4 md:p-6">
      <!-- Título y fecha -->
      <header class="mb-6">
        <h1 class="text-2xl md:text-3xl font-bold text-[#1e3a5f]">Panel de Control</h1>
        <p class="text-sm text-gray-500 mt-1">{{ fechaActual }}</p>
      </header>

      <!-- Mensaje de error global -->
      <div
        v-if="error"
        class="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm"
      >
        {{ error }}
      </div>

      <!-- Tarjetas superiores: grid 4 cols desktop, 2 tablet -->
      <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <!-- Skeleton mientras carga -->
        <template v-if="cargando">
          <Card v-for="i in 4" :key="'sk-' + i" class="!shadow-sm">
            <template #content>
              <div class="flex items-center gap-3">
                <Skeleton shape="circle" size="3rem" />
                <div class="flex-1">
                  <Skeleton width="8rem" height="1rem" class="mb-2" />
                  <Skeleton width="4rem" height="1.75rem" />
                </div>
              </div>
            </template>
          </Card>
        </template>

        <!-- Tarjetas reales -->
        <template v-else>
          <!-- 1. Ingresadas hoy -->
          <div
            class="rounded-lg shadow-sm overflow-hidden border-l-4"
            style="border-left-color: #2d6a9f"
          >
            <Card class="!shadow-none !border-0 !rounded-none" style="background-color: #f8fafc">
              <template #content>
                <div class="flex items-center gap-3">
                  <i class="pi pi-inbox text-2xl" style="color: #2d6a9f" />
                  <div>
                    <p class="text-sm font-medium text-gray-500 uppercase tracking-wide">
                      Ingresadas hoy
                    </p>
                    <p class="text-2xl font-bold text-gray-900">{{ ingresadasHoy }}</p>
                  </div>
                </div>
              </template>
            </Card>
          </div>

          <!-- 2. En proceso -->
          <div
            class="rounded-lg shadow-sm overflow-hidden border-l-4"
            style="border-left-color: #f59e0b"
          >
            <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
              <template #content>
                <div class="flex items-center gap-3">
                  <i class="pi pi-spinner pi-spin text-2xl" style="color: #f59e0b" />
                  <div>
                    <p class="text-sm font-medium text-gray-500 uppercase tracking-wide">
                      En proceso
                    </p>
                    <p class="text-2xl font-bold text-gray-900">{{ enProceso }}</p>
                  </div>
                </div>
              </template>
            </Card>
          </div>

          <!-- 3. Atrasadas -->
          <div
            class="rounded-lg shadow-sm overflow-hidden border-l-4"
            style="border-left-color: #e74c3c"
          >
            <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
              <template #content>
                <div class="flex items-center gap-3">
                  <i class="pi pi-exclamation-triangle text-2xl" style="color: #e74c3c" />
                  <div>
                    <p class="text-sm font-medium text-gray-500 uppercase tracking-wide">
                      Atrasadas
                    </p>
                    <p
                      class="text-2xl font-bold"
                      :class="atrasadas > 0 ? 'text-[#e74c3c]' : 'text-gray-900'"
                    >
                      {{ atrasadas }}
                    </p>
                  </div>
                </div>
              </template>
            </Card>
          </div>

          <!-- 4. Resueltas este mes -->
          <div
            class="rounded-lg shadow-sm overflow-hidden border-l-4"
            style="border-left-color: #27ae60"
          >
            <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
              <template #content>
                <div class="flex items-center gap-3">
                  <i class="pi pi-check-circle text-2xl" style="color: #27ae60" />
                  <div>
                    <p class="text-sm font-medium text-gray-500 uppercase tracking-wide">
                      Resueltas este mes
                    </p>
                    <p class="text-2xl font-bold text-gray-900">{{ resueltasEsteMes }}</p>
                  </div>
                </div>
              </template>
            </Card>
          </div>
        </template>
      </section>

      <!-- Paneles inferiores: 2 columnas desktop, 1 móvil -->
      <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Panel izquierdo: Mis notas pendientes -->
        <Card class="!bg-white !border !border-gray-200 !shadow-sm">
          <template #title>
            <span class="text-lg font-semibold text-[#1e3a5f]">Mis notas pendientes</span>
          </template>
          <template #content>
            <template v-if="cargando">
              <div class="space-y-3">
                <Skeleton width="100%" height="2.5rem" v-for="i in 4" :key="i" />
              </div>
            </template>
            <template v-else-if="pendientes.length === 0">
              <div class="py-8 text-center text-gray-500">
                <i class="pi pi-inbox text-4xl mb-2 block opacity-60" />
                <p>No tenés notas pendientes</p>
              </div>
            </template>
            <template v-else>
              <ul class="space-y-3">
                <li
                  v-for="nota in pendientes"
                  :key="nota.id"
                  class="flex flex-wrap items-center gap-2 py-2 border-b border-gray-100 last:border-0"
                >
                  <span class="font-mono text-sm text-gray-700">{{
                    nota.numero_nota_interno
                  }}</span>
                  <span class="text-gray-800 flex-1 min-w-0" :title="nota.tema">{{
                    truncar(nota.tema, 40)
                  }}</span>
                  <Tag
                    :value="labelEstado(nota.estado)"
                    :style="{
                      background: colorEstado(nota.estado),
                      color: 'white',
                      border: 'none',
                    }"
                    class="!text-xs"
                  />
                  <span
                    v-if="nota.fecha_limite"
                    class="text-sm"
                    :class="nota.atrasada ? 'text-red-600 font-medium' : 'text-gray-500'"
                  >
                    {{ formatoFecha(nota.fecha_limite) }}
                    <Badge v-if="nota.atrasada" value="Atrasada" severity="danger" class="ml-1" />
                  </span>
                </li>
              </ul>
              <div class="mt-4 pt-3 border-t border-gray-100">
                <Button
                  label="Ver todas"
                  link
                  size="small"
                  class="p-0 text-[#1e3a5f] font-medium"
                  @click="irA('/notas/pendientes')"
                />
              </div>
            </template>
          </template>
        </Card>

        <!-- Panel derecho: Últimas notas ingresadas -->
        <Card class="!bg-white !border !border-gray-200 !shadow-sm">
          <template #title>
            <span class="text-lg font-semibold text-[#1e3a5f]">Últimas notas ingresadas</span>
          </template>
          <template #content>
            <template v-if="cargando">
              <div class="space-y-3">
                <Skeleton width="100%" height="2.5rem" v-for="i in 4" :key="i" />
              </div>
            </template>
            <template v-else-if="ultimasIngresadas.length === 0">
              <div class="py-8 text-center text-gray-500">
                <i class="pi pi-inbox text-4xl mb-2 block opacity-60" />
                <p>No hay notas ingresadas</p>
              </div>
            </template>
            <template v-else>
              <ul class="space-y-3">
                <li
                  v-for="nota in ultimasIngresadas"
                  :key="nota.id"
                  class="flex flex-wrap items-center gap-2 py-2 border-b border-gray-100 last:border-0"
                >
                  <span class="font-mono text-sm text-gray-700">{{
                    nota.numero_nota_interno
                  }}</span>
                  <span class="text-gray-800 flex-1 min-w-0" :title="nota.tema">{{
                    truncar(nota.tema, 40)
                  }}</span>
                  <span class="text-sm text-gray-500">—</span>
                  <span class="text-sm text-gray-500">{{ haceCuanto(nota.fecha_ingreso) }}</span>
                </li>
              </ul>
              <div class="mt-4 pt-3 border-t border-gray-100">
                <Button
                  label="Ver todas"
                  link
                  size="small"
                  class="p-0 text-[#1e3a5f] font-medium"
                  @click="irA('/notas')"
                />
              </div>
            </template>
          </template>
        </Card>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100%;
}
</style>
