<script setup>
/**
 * AdminView — Panel de administración con reportes y auditoría.
 * Solo visible para ADMINISTRADOR.
 */
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { reportesService } from '@/services/notasService'
import { haceCuanto, formatoFechaHora, toArray } from '@/utils/notas'

const router = useRouter()

// Tabs: 'reportes' | 'auditoria'
const tabActivo = ref('reportes')

// Datos
const notasPorSector = ref([])
const notasPorOperador = ref([])
const auditoria = ref([])
const cargandoReportes = ref(true)
const cargandoAuditoria = ref(false)
const error = ref(null)

/** ID de nota cuya(s) fila(s) de auditoría se resaltan al volver del detalle (scoped CSS vía v-bind). */
const filaDestacadaId = ref(null)

// Iconos por tipo de evento
const iconoTipoEvento = (tipo) => {
  const map = {
    CREACION: { icon: 'pi-plus-circle', color: '#059669' },
    CAMBIO_ESTADO: { icon: 'pi-refresh', color: '#1d4ed8' },
    REASIGNACION: { icon: 'pi-arrow-right-arrow-left', color: '#d97706' },
    ASIGNACION: { icon: 'pi-user-plus', color: '#1d4ed8' },
    ACTUALIZACION: { icon: 'pi-pencil', color: '#475569' },
    ANULACION: { icon: 'pi-times-circle', color: '#dc2626' },
    ARCHIVADO: { icon: 'pi-archive', color: '#475569' },
    ADJUNTO: { icon: 'pi-paperclip', color: '#475569' },
    RESOLUCION_CARGADA: { icon: 'pi-file', color: '#059669' },
    DERIVACION_DESPACHO: { icon: 'pi-send', color: '#475569' },
    DISTRIBUCION_SECTOR: { icon: 'pi-share-alt', color: '#475569' },
  }
  return map[tipo] || { icon: 'pi-info-circle', color: '#475569' }
}

// Máximo total para barra de progreso (sectores)
const maxTotalSector = computed(() => {
  const totals = notasPorSector.value.map((s) => s.total)
  return totals.length ? Math.max(...totals, 1) : 1
})

function porcentaje(total) {
  return Math.round((total / maxTotalSector.value) * 100)
}

async function cargarReportes() {
  cargandoReportes.value = true
  error.value = null
  try {
    const [sectores, operadores] = await Promise.all([
      reportesService.getReportesPorSector(),
      reportesService.getReportesPorOperador(),
    ])
    notasPorSector.value = toArray(sectores)
    notasPorOperador.value = toArray(operadores)
  } catch (e) {
    error.value = e?.data?.detalle || e?.data?.detail || e?.message || 'Error al cargar reportes.'
  } finally {
    cargandoReportes.value = false
  }
}

async function cargarAuditoria() {
  cargandoAuditoria.value = true
  error.value = null
  try {
    const res = await reportesService.getAuditoria()
    auditoria.value = toArray(res)
  } catch (e) {
    error.value = e?.data?.detalle || e?.data?.detail || e?.message || 'Error al cargar auditoría.'
  } finally {
    cargandoAuditoria.value = false
  }
}

function seleccionarTab(tab) {
  tabActivo.value = tab
  if (tab === 'auditoria' && auditoria.value.length === 0 && !cargandoAuditoria.value) {
    cargarAuditoria()
  }
}

function irANota(notaId) {
  sessionStorage.setItem('admin-auditoria-scroll', String(document.documentElement.scrollTop || 0))
  sessionStorage.setItem('admin-auditoria-nota-id', String(notaId))
  router.push(`/notas/${notaId}`)
}

onMounted(async () => {
  await Promise.all([cargarReportes(), cargarAuditoria()])

  const savedScroll = sessionStorage.getItem('admin-auditoria-scroll')
  if (savedScroll) {
    tabActivo.value = 'auditoria'
    await nextTick()
    document.documentElement.scrollTop = parseInt(savedScroll, 10) || 0
    sessionStorage.removeItem('admin-auditoria-scroll')
  }

  const notaDestacadaId = sessionStorage.getItem('admin-auditoria-nota-id')
  if (notaDestacadaId) {
    tabActivo.value = 'auditoria'
    await nextTick()
    setTimeout(() => {
      const idNum = Number.parseInt(notaDestacadaId, 10)
      if (!Number.isNaN(idNum)) {
        filaDestacadaId.value = idNum
        setTimeout(() => {
          filaDestacadaId.value = null
        }, 3500)
      }
      sessionStorage.removeItem('admin-auditoria-nota-id')
    }, 200)
  }
})
</script>

<template>
  <div class="admin-view min-h-full" style="background-color: #eef2f7">
    <div class="p-4 md:p-6">
      <header class="mb-6">
        <h1 class="text-2xl md:text-3xl font-bold text-[#1e3a5f]">Administración</h1>
      </header>

      <!-- Tabs de navegación -->
      <div class="flex gap-2 mb-6">
        <button
          type="button"
          :class="[
            'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
            tabActivo === 'reportes'
              ? 'bg-[#1e3a5f] text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200',
          ]"
          @click="seleccionarTab('reportes')"
        >
          <i class="pi pi-chart-bar mr-2" />
          Reportes
        </button>
        <button
          type="button"
          :class="[
            'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
            tabActivo === 'auditoria'
              ? 'bg-[#1e3a5f] text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200',
          ]"
          @click="seleccionarTab('auditoria')"
        >
          <i class="pi pi-search mr-2" />
          Auditoría
        </button>
      </div>

      <div
        v-if="error"
        class="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm"
      >
        {{ error }}
      </div>

      <!-- TAB REPORTES -->
      <div v-if="tabActivo === 'reportes'" class="space-y-6">
        <div v-if="cargandoReportes" class="py-8">
          <ProgressBar mode="indeterminate" style="height: 4px" />
        </div>

        <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- SECCIÓN 1 — Notas por sector -->
          <div class="bg-white rounded-xl shadow-sm overflow-hidden">
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-[#1e3a5f]">Notas por sector</h2>
            </div>
            <div class="p-4 overflow-x-auto">
              <table class="w-full text-sm tabla-reporte">
                <thead>
                  <tr class="border-b border-gray-200">
                    <th class="text-left py-2 px-3 font-medium text-gray-700">Sector</th>
                    <th class="text-right py-2 px-3 font-medium text-gray-700">Total</th>
                    <th class="text-right py-2 px-3 font-medium text-gray-700">Activas</th>
                    <th class="text-right py-2 px-3 font-medium text-gray-700">Resueltas</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="s in notasPorSector"
                    :key="s.numero + s.sector"
                    class="border-b border-gray-100"
                  >
                    <td class="py-3 px-3">
                      <div class="font-medium text-gray-800">{{ s.sector }}</div>
                      <div class="text-xs text-gray-500">{{ s.numero }}</div>
                    </td>
                    <td class="py-3 px-3 text-right">
                      <div class="w-full max-w-[120px] ml-auto">
                        <div class="w-full bg-gray-200 rounded-full h-2 mb-1">
                          <div
                            class="h-2 rounded-full bg-[#1e3a5f] transition-all"
                            :style="{ width: porcentaje(s.total) + '%' }"
                          />
                        </div>
                        <span class="font-medium">{{ s.total }}</span>
                      </div>
                    </td>
                    <td class="py-3 px-3 text-right text-gray-700">
                      {{ (s.ingresadas || 0) + (s.en_proceso || 0) }}
                    </td>
                    <td class="py-3 px-3 text-right text-gray-700">
                      {{ s.resueltas || 0 }}
                    </td>
                  </tr>
                  <tr v-if="!notasPorSector.length">
                    <td colspan="4" class="py-8 text-center text-gray-500">No hay datos</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- SECCIÓN 2 — Notas por operador -->
          <div class="bg-white rounded-xl shadow-sm overflow-hidden">
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-[#1e3a5f]">Notas por operador</h2>
            </div>
            <div class="p-4 overflow-x-auto">
              <table class="w-full text-sm tabla-reporte">
                <thead>
                  <tr class="border-b border-gray-200">
                    <th class="text-left py-2 px-3 font-medium text-gray-700">Operador</th>
                    <th class="text-right py-2 px-3 font-medium text-gray-700">Pendientes</th>
                    <th class="text-right py-2 px-3 font-medium text-gray-700">En proceso</th>
                    <th class="text-right py-2 px-3 font-medium text-gray-700">Resueltas</th>
                    <th class="text-right py-2 px-3 font-medium text-gray-700">Total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="op in notasPorOperador"
                    :key="op.legajo"
                    class="border-b border-gray-100"
                  >
                    <td class="py-3 px-3">
                      <div class="font-medium text-gray-800">{{ op.operador }}</div>
                      <div class="text-xs text-gray-500">{{ op.legajo }}</div>
                    </td>
                    <td class="py-3 px-3 text-right">
                      <span
                        v-if="op.pendientes"
                        class="px-2 py-0.5 rounded text-xs font-medium text-white"
                        style="background-color: #6366f1"
                      >
                        {{ op.pendientes }}
                      </span>
                      <span v-else class="text-gray-400">0</span>
                    </td>
                    <td class="py-3 px-3 text-right">
                      <span
                        v-if="op.en_proceso"
                        class="px-2 py-0.5 rounded text-xs font-medium text-white"
                        style="background-color: #1d4ed8"
                      >
                        {{ op.en_proceso }}
                      </span>
                      <span v-else class="text-gray-400">0</span>
                    </td>
                    <td class="py-3 px-3 text-right">
                      <span
                        v-if="op.resueltas"
                        class="px-2 py-0.5 rounded text-xs font-medium text-white"
                        style="background-color: #059669"
                      >
                        {{ op.resueltas }}
                      </span>
                      <span v-else class="text-gray-400">0</span>
                    </td>
                    <td class="py-3 px-3 text-right font-medium">{{ op.total }}</td>
                  </tr>
                  <tr v-if="!notasPorOperador.length">
                    <td colspan="5" class="py-8 text-center text-gray-500">No hay datos</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB AUDITORÍA -->
      <div v-if="tabActivo === 'auditoria'" class="space-y-6">
        <div v-if="cargandoAuditoria" class="py-8">
          <ProgressBar mode="indeterminate" style="height: 4px" />
        </div>

        <div v-else class="bg-white rounded-xl shadow-sm overflow-hidden">
          <div class="p-4 border-b border-gray-100">
            <h2 class="text-lg font-semibold text-[#1e3a5f]">Auditoría del sistema</h2>
            <p class="text-sm text-gray-500 mt-1">Últimas 100 acciones registradas</p>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm tabla-auditoria">
              <thead>
                <tr class="border-b border-gray-200 bg-gray-50">
                  <th class="text-left py-2 px-3 font-medium text-gray-700">Fecha y hora</th>
                  <th class="text-left py-2 px-3 font-medium text-gray-700">Usuario</th>
                  <th class="text-left py-2 px-3 font-medium text-gray-700">Nota</th>
                  <th class="text-left py-2 px-3 font-medium text-gray-700">Acción</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in auditoria"
                  :key="item.id"
                  :data-nota-id="item.nota_id"
                  :class="[
                    'border-b border-gray-100',
                    {
                      'fila-destacada':
                        filaDestacadaId !== null &&
                        Number(item.nota_id) === Number(filaDestacadaId),
                    },
                  ]"
                >
                  <td class="py-3 px-3">
                    <span v-tooltip.top="formatoFechaHora(item.fecha_hora)" class="cursor-help">
                      {{ haceCuanto(item.fecha_hora) }}
                    </span>
                  </td>
                  <td class="py-3 px-3 text-gray-800">{{ item.usuario }}</td>
                  <td class="py-3 px-3">
                    <span
                      v-if="item.nota_id"
                      class="font-mono text-sm text-[#1e3a5f] hover:underline cursor-pointer font-bold"
                      @click="irANota(item.nota_id)"
                    >
                      {{ item.nota }}
                    </span>
                    <span v-else class="text-gray-500">{{ item.nota || '—' }}</span>
                  </td>
                  <td class="py-3 px-3">
                    <div class="flex items-center gap-2">
                      <i
                        :class="['pi', iconoTipoEvento(item.tipo_evento).icon, 'text-sm']"
                        :style="{ color: iconoTipoEvento(item.tipo_evento).color }"
                      />
                      <span class="text-gray-700">{{ item.descripcion_cambio || '—' }}</span>
                    </div>
                  </td>
                </tr>
                <tr v-if="!auditoria.length">
                  <td colspan="4" class="py-8 text-center text-gray-500">
                    No hay registros de auditoría
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-view {
  min-height: 100%;
}

.tabla-reporte tbody tr {
  border-left: 3px solid transparent;
  transition: all 0.15s;
}

.tabla-reporte tbody tr:hover {
  background: #d2d7e4;
}

.fila-destacada {
  background-color: #d2d7e4 !important;
  border-left: 3px solid #1e3a5f !important;
  transition: all6s ease;
}
</style>
