<script setup>
/**
 * DashboardView — Dashboard diferente por rol.
 * SUPERVISOR/ADMINISTRADOR: 6 tarjetas + panel "Últimas notas ingresadas"
 * OPERADOR: 3 tarjetas + panel "Mis notas pendientes"
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get } from '@/api/cliente'
import { useAuthStore } from '@/stores/auth'
import TablaNotasSimple from '@/components/TablaNotasSimple.vue'
import { esDelMesActual } from '@/utils/notas'

const router = useRouter()
const auth = useAuthStore()

// Rol del usuario actual
const rol = computed(() => auth.usuario?.rol ?? null)
const esSupervisorOAdmin = computed(() => ['SUPERVISOR', 'ADMINISTRADOR'].includes(rol.value))
const esOperador = computed(() => rol.value === 'OPERADOR')

// Estado del dashboard
const cargando = ref(true)
const error = ref(null)

// Datos para SUPERVISOR/ADMINISTRADOR (6 tarjetas)
const ingresadas = ref(0)
const enProceso = ref(0)
const sinAsignar = ref(0)
const atrasadas = ref(0)
const enEspera = ref(0)
const resueltasEsteMes = ref(0)
const ultimasIngresadas = ref([])

// Datos para OPERADOR (3 tarjetas)
const misAsignadas = ref(0)
const misEnProceso = ref(0)
const misEnEspera = ref(0)
const pendientes = ref([])

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
  return `${dias[ahora.getDay()]}, ${ahora.getDate()} de ${meses[ahora.getMonth()]} de ${ahora.getFullYear()}`
})

// Normalizar respuesta API a array
function toArray(r) {
  return Array.isArray(r) ? r : r?.results || []
}

// Ordenar por prioridad: URGENTE, ALTA, NORMAL, BAJA
const ordenPrioridad = { URGENTE: 0, ALTA: 1, NORMAL: 2, MEDIA: 2, BAJA: 3 }
function ordenarPorPrioridad(notas) {
  return [...notas].sort((a, b) => {
    const pa = ordenPrioridad[a.prioridad] ?? 4
    const pb = ordenPrioridad[b.prioridad] ?? 4
    return pa - pb
  })
}

async function cargarDashboardSupervisor() {
  const [rIngresadas, rEnProceso, rAtrasadas, rEnEspera, rLista, rResueltas, rArchivadas] =
    await Promise.all([
      get('/api/notas/?estado=INGRESADA'),
      get('/api/notas/?estado=EN_PROCESO'),
      get('/api/notas/atrasadas/'),
      get('/api/notas/?estado=EN_ESPERA'),
      get('/api/notas/'),
      get('/api/notas/?estado=RESUELTA'),
      get('/api/notas/?estado=ARCHIVADA'),
    ])

  const listaIngresadas = toArray(rIngresadas)
  ingresadas.value = listaIngresadas.length
  sinAsignar.value = listaIngresadas.filter((n) => !n.responsable || !n.responsable.id).length

  enProceso.value = toArray(rEnProceso).length
  atrasadas.value = toArray(rAtrasadas).length
  enEspera.value = toArray(rEnEspera).length

  const listaGeneral = toArray(rLista)
  ultimasIngresadas.value = listaGeneral.slice(0, 5)

  const listasResueltas = [...toArray(rResueltas), ...toArray(rArchivadas)]
  resueltasEsteMes.value = listasResueltas.filter((n) => esDelMesActual(n.fecha_ingreso)).length
}

async function cargarDashboardOperador() {
  const [rPendientes, rAsignadas, rEnProceso, rEnEspera] = await Promise.all([
    get('/api/notas/pendientes/'),
    get('/api/notas/?estado=ASIGNADA'),
    get('/api/notas/?estado=EN_PROCESO'),
    get('/api/notas/?estado=EN_ESPERA'),
  ])

  const userId = auth.usuario?.id
  const esMia = (n) => n.responsable?.id === userId || n.responsable === userId

  misAsignadas.value = toArray(rAsignadas).filter(esMia).length
  misEnProceso.value = toArray(rEnProceso).filter(esMia).length
  misEnEspera.value = toArray(rEnEspera).filter(esMia).length

  const todasPendientes = ordenarPorPrioridad(toArray(rPendientes))
  pendientes.value = todasPendientes.slice(0, 5)
}

async function cargarDashboard() {
  cargando.value = true
  error.value = null
  try {
    if (esSupervisorOAdmin.value) {
      await cargarDashboardSupervisor()
    } else if (esOperador.value) {
      await cargarDashboardOperador()
    } else {
      // CONSULTOR u otro: dashboard mínimo (solo últimas ingresadas)
      const rLista = await get('/api/notas/')
      ultimasIngresadas.value = toArray(rLista).slice(0, 5)
    }
  } catch (e) {
    error.value = e.data?.detalle || e.message || 'Error al cargar el panel de control.'
  } finally {
    cargando.value = false
  }
}

// Tarjeta reutilizable con estilos
const TARJETA_COLORES = {
  INGRESADAS: '#475569',
  EN_PROCESO: '#1d4ed8',
  SIN_ASIGNAR: '#e11d48',
  ATRASADAS: '#e11d48',
  EN_ESPERA: '#d97706',
  RESUELTAS: '#059669',
  MIS_ASIGNADAS: '#6366f1',
  MIS_EN_PROCESO: '#1d4ed8',
  MIS_EN_ESPERA: '#d97706',
}

onMounted(cargarDashboard)
</script>

<template>
  <div class="dashboard min-h-full" style="background-color: #eef2f7">
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

      <!-- ========== DASHBOARD SUPERVISOR / ADMINISTRADOR ========== -->
      <template v-if="esSupervisorOAdmin">
        <!-- 6 tarjetas superiores -->
        <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
          <template v-if="cargando">
            <Card v-for="i in 6" :key="'sk-' + i" class="!shadow-sm">
              <template #content>
                <div class="flex items-center gap-3">
                  <Skeleton shape="circle" size="3rem" />
                  <div class="flex-1">
                    <Skeleton width="6rem" height="1rem" class="mb-2" />
                    <Skeleton width="3rem" height="1.75rem" />
                  </div>
                </div>
              </template>
            </Card>
          </template>
          <template v-else>
            <!-- 1. INGRESADAS -->
            <div
              class="rounded-lg shadow-sm overflow-hidden border-l-4 hover:shadow-md transition-shadow cursor-pointer"
              style="border-left-color: #475569"
              @click="router.push('/notas?estado=INGRESADA')"
            >
              <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
                <template #content>
                  <div class="flex items-center gap-3">
                    <i class="pi pi-inbox text-2xl" style="color: #475569" />
                    <div>
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Ingresadas
                      </p>
                      <p class="text-2xl font-bold text-gray-900">{{ ingresadas }}</p>
                    </div>
                  </div>
                </template>
              </Card>
            </div>
            <!-- 2. EN PROCESO -->
            <div
              class="rounded-lg shadow-sm overflow-hidden border-l-4 hover:shadow-md transition-shadow cursor-pointer"
              style="border-left-color: #1d4ed8"
              @click="router.push('/notas?estado=EN_PROCESO')"
            >
              <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
                <template #content>
                  <div class="flex items-center gap-3">
                    <i class="pi pi-spinner pi-spin text-2xl" style="color: #1d4ed8" />
                    <div>
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        En proceso
                      </p>
                      <p class="text-2xl font-bold text-gray-900">{{ enProceso }}</p>
                    </div>
                  </div>
                </template>
              </Card>
            </div>
            <!-- 3. SIN ASIGNAR -->
            <div
              class="rounded-lg shadow-sm overflow-hidden border-l-4 hover:shadow-md transition-shadow cursor-pointer"
              style="border-left-color: #e11d48"
              @click="router.push('/notas?sin_asignar=true')"
            >
              <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
                <template #content>
                  <div class="flex items-center gap-3">
                    <i class="pi pi-user-minus text-2xl" style="color: #e11d48" />
                    <div>
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Sin asignar
                      </p>
                      <p
                        class="text-2xl font-bold"
                        :class="sinAsignar > 0 ? 'text-[#e11d48]' : 'text-gray-900'"
                      >
                        {{ sinAsignar }}
                      </p>
                    </div>
                  </div>
                </template>
              </Card>
            </div>
            <!-- 4. ATRASADAS -->
            <div
              class="rounded-lg shadow-sm overflow-hidden border-l-4 hover:shadow-md transition-shadow cursor-pointer"
              style="border-left-color: #e11d48"
              @click="router.push('/notas?atrasadas=true')"
            >
              <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
                <template #content>
                  <div class="flex items-center gap-3">
                    <i class="pi pi-exclamation-triangle text-2xl" style="color: #e11d48" />
                    <div>
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Atrasadas
                      </p>
                      <p
                        class="text-2xl font-bold"
                        :class="atrasadas > 0 ? 'text-[#e11d48]' : 'text-gray-900'"
                      >
                        {{ atrasadas }}
                      </p>
                    </div>
                  </div>
                </template>
              </Card>
            </div>
            <!-- 5. EN ESPERA -->
            <div
              class="rounded-lg shadow-sm overflow-hidden border-l-4 hover:shadow-md transition-shadow cursor-pointer"
              style="border-left-color: #d97706"
              @click="router.push('/notas?estado=EN_ESPERA')"
            >
              <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
                <template #content>
                  <div class="flex items-center gap-3">
                    <i class="pi pi-clock text-2xl" style="color: #d97706" />
                    <div>
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        En espera
                      </p>
                      <p class="text-2xl font-bold text-gray-900">{{ enEspera }}</p>
                    </div>
                  </div>
                </template>
              </Card>
            </div>
            <!-- 6. RESUELTAS ESTE MES -->
            <div
              class="rounded-lg shadow-sm overflow-hidden border-l-4 hover:shadow-md transition-shadow cursor-pointer"
              style="border-left-color: #059669"
              @click="router.push('/notas?estado=RESUELTA')"
            >
              <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
                <template #content>
                  <div class="flex items-center gap-3">
                    <i class="pi pi-check-circle text-2xl" style="color: #059669" />
                    <div>
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">
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

        <!-- Panel inferior: Últimas notas ingresadas -->
        <section class="grid grid-cols-1">
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
                <TablaNotasSimple
                  :notas="ultimasIngresadas"
                  :cargando="cargando"
                  desde="inicio"
                  :clickeable="true"
                />
              </template>
            </template>
          </Card>
        </section>
      </template>

      <!-- ========== DASHBOARD OPERADOR ========== -->
      <template v-else-if="esOperador">
        <!-- 3 tarjetas superiores -->
        <section class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <template v-if="cargando">
            <Card v-for="i in 3" :key="'sk-' + i" class="!shadow-sm">
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
          <template v-else>
            <!-- 1. MIS ASIGNADAS -->
            <div
              class="rounded-lg shadow-sm overflow-hidden border-l-4 hover:shadow-md transition-shadow cursor-pointer"
              style="border-left-color: #6366f1"
              @click="router.push('/mis-notas?estado=ASIGNADA')"
            >
              <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
                <template #content>
                  <div class="flex items-center gap-3">
                    <i class="pi pi-inbox text-2xl" style="color: #6366f1" />
                    <div>
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Mis asignadas
                      </p>
                      <p class="text-2xl font-bold text-gray-900">{{ misAsignadas }}</p>
                    </div>
                  </div>
                </template>
              </Card>
            </div>
            <!-- 2. MIS EN PROCESO -->
            <div
              class="rounded-lg shadow-sm overflow-hidden border-l-4 hover:shadow-md transition-shadow cursor-pointer"
              style="border-left-color: #1d4ed8"
              @click="router.push('/mis-notas?estado=EN_PROCESO')"
            >
              <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
                <template #content>
                  <div class="flex items-center gap-3">
                    <i class="pi pi-spinner pi-spin text-2xl" style="color: #1d4ed8" />
                    <div>
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Mis en proceso
                      </p>
                      <p class="text-2xl font-bold text-gray-900">{{ misEnProceso }}</p>
                    </div>
                  </div>
                </template>
              </Card>
            </div>
            <!-- 3. MIS EN ESPERA -->
            <div
              class="rounded-lg shadow-sm overflow-hidden border-l-4 hover:shadow-md transition-shadow cursor-pointer"
              style="border-left-color: #d97706"
              @click="router.push('/mis-notas?estado=EN_ESPERA')"
            >
              <Card class="!shadow-none !border-0 !rounded-none" style="background-color: white">
                <template #content>
                  <div class="flex items-center gap-3">
                    <i class="pi pi-clock text-2xl" style="color: #d97706" />
                    <div>
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Mis en espera
                      </p>
                      <p class="text-2xl font-bold text-gray-900">{{ misEnEspera }}</p>
                    </div>
                  </div>
                </template>
              </Card>
            </div>
          </template>
        </section>

        <!-- Panel inferior: Mis notas pendientes -->
        <section class="grid grid-cols-1">
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
                <TablaNotasSimple
                  :notas="pendientes"
                  :cargando="cargando"
                  desde="inicio"
                  :clickeable="true"
                />
              </template>
            </template>
          </Card>
        </section>
      </template>

      <!-- ========== CONSULTOR u otro rol ========== -->
      <template v-else>
        <section class="grid grid-cols-1">
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
                <TablaNotasSimple
                  :notas="ultimasIngresadas"
                  :cargando="cargando"
                  desde="inicio"
                  :clickeable="true"
                />
              </template>
            </template>
          </Card>
        </section>
      </template>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100%;
}
</style>
