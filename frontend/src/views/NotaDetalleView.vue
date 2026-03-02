<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { get, post } from '@/api/cliente'
import { useToast } from 'primevue/usetoast'
import { useAuthStore } from '@/stores/auth'
import {
  formatoFecha,
  formatoFechaHora,
  colorEstado,
  labelEstado,
  colorPrioridad,
  labelPrioridad,
} from '@/utils/notas'

const route = useRoute()
const router = useRouter()
const toast = useToast()

// Estado
const nota = ref(null)
const sectores = ref([])
const usuarios = ref([])
const cargando = ref(true)
const error = ref(null)
const enviandoAccion = ref(false)

// Dialogs
const dialogAsignar = ref(false)
const dialogMotivo = ref(false)

// Formularios de dialogs
const asignarResponsableId = ref(null)
const asignarMotivo = ref('')
const motivoTexto = ref('')
const accionPendiente = ref(null) // { tipo: 'asignar'|'reasignar'|'en_espera'|'devolver', estado_nuevo }

// Usuarios para dropdown (excluir CONSULTOR)
const usuariosParaAsignar = computed(() =>
  usuarios.value
    .filter((u) => u.rol !== 'CONSULTOR')
    .map((u) => ({
      ...u,
      nombre_completo:
        u.nombre_completo || `${u.apellido || ''}, ${u.nombres || ''}`.trim() || u.email,
    })),
)

const notaId = computed(() => route.params.id)

// Sector de origen (la API puede devolver id; resolvemos con lista de sectores)
const sectorOrigenDisplay = computed(() => {
  if (!nota.value) return '—'
  const so = nota.value.sector_origen
  if (typeof so === 'object' && so !== null) return `${so.numero} — ${so.nombre}`
  const id = typeof so === 'number' ? so : parseInt(so, 10)
  if (!id) return '—'
  const s = sectores.value.find((sec) => sec.id === id)
  return s ? `${s.numero} — ${s.nombre}` : `Sector ${id}`
})

// Usuario actual (store de auth)
const authStore = useAuthStore()
const usuarioActual = computed(() => authStore.usuario ?? null)

const esSupervisorOAdmin = computed(() =>
  ['SUPERVISOR', 'ADMINISTRADOR'].includes(usuarioActual.value?.rol),
)

const esResponsable = computed(() => {
  const idUsuario = Number(usuarioActual.value?.id)
  const idResponsable = Number(nota.value?.responsable?.id)
  console.log('DEBUG:', { idUsuario, idResponsable })
  return idUsuario === idResponsable
})

// Iniciales del responsable para avatar
const responsableIniciales = computed(() => {
  const r = nota.value?.responsable
  if (!r || typeof r !== 'string') return '—'
  const partes = r.split(',')
  if (partes.length >= 2) {
    const ap = partes[0].trim()
    const nom = partes[1].trim()
    return (ap[0] || '') + (nom[0] || '')
  }
  return r.slice(0, 2).toUpperCase()
})

// Historial ordenado del más reciente al más antiguo (la API ya puede venir ordenado)
const historialOrdenado = computed(() => {
  const h = nota.value?.historial ?? []
  return [...h].sort((a, b) => new Date(b.fecha_hora) - new Date(a.fecha_hora))
})

// Ícono y color por tipo de evento
function iconoEvento(tipo) {
  const map = {
    CREACION: 'pi-plus-circle',
    CAMBIO_ESTADO: 'pi-arrow-right',
    ASIGNACION: 'pi-user-plus',
    REASIGNACION: 'pi-user-edit',
    ACTUALIZACION: 'pi-pencil',
    ANULACION: 'pi-times-circle',
    ARCHIVADO: 'pi-archive',
    DERIVACION_DESPACHO: 'pi-send',
    RESOLUCION_CARGADA: 'pi-file',
    DISTRIBUCION_SECTOR: 'pi-share-alt',
  }
  return map[tipo] || 'pi-circle'
}

function colorIconoEvento(tipo) {
  const map = {
    CREACION: '#059669',
    CAMBIO_ESTADO: '#0ea5e9',
    REASIGNACION: '#f97316',
    ACTUALIZACION: '#64748b',
    ANULACION: '#dc2626',
    ARCHIVADO: '#94a3b8',
  }
  return map[tipo] || '#64748b'
}

// Labels canal de ingreso
const LABELS_CANAL = {
  PRESENCIAL: 'Presencial',
  EMAIL: 'Email',
  TELEFONO: 'Teléfono',
  SISTEMA: 'Sistema',
  OTRO: 'Otro',
}
function labelCanal(canal) {
  return canal ? LABELS_CANAL[canal] || canal : '—'
}

async function cargarNota() {
  if (!notaId.value) return
  cargando.value = true
  error.value = null
  try {
    nota.value = await get(`/api/notas/${notaId.value}/`)
  } catch (e) {
    error.value = e.data?.detalle || e.data?.error || e.message || 'Error al cargar la nota.'
    nota.value = null
  } finally {
    cargando.value = false
  }
}

async function cargarSectores() {
  try {
    const res = await get('/api/sectores/')
    sectores.value = Array.isArray(res) ? res : res.results || []
  } catch {
    sectores.value = []
  }
}

async function cargarUsuarios() {
  try {
    const res = await get('/api/usuarios/?activos=true')
    usuarios.value = Array.isArray(res) ? res : res.results || []
  } catch {
    usuarios.value = []
  }
}

function volverANotas() {
  router.push('/notas')
}

// Cambio de estado
async function ejecutarCambioEstado(payload) {
  enviandoAccion.value = true
  try {
    await post(`/api/notas/${notaId.value}/cambiar_estado/`, payload)
    toast.add({
      severity: 'success',
      summary: 'Estado actualizado',
      detail: 'La nota se actualizó correctamente.',
    })
    await cargarNota()
    cerrarDialogs()
  } catch (e) {
    const msg = e.data?.detalle || e.data?.error || e.message || 'Error al cambiar el estado.'
    toast.add({ severity: 'error', summary: 'Error', detail: msg })
  } finally {
    enviandoAccion.value = false
  }
}

function cerrarDialogs() {
  dialogAsignar.value = false
  dialogMotivo.value = false
  accionPendiente.value = null
  asignarResponsableId.value = null
  asignarMotivo.value = ''
  motivoTexto.value = ''
}

// Dialog Asignar: para Asignar (INGRESADA) y Reasignar (ASIGNADA)
function abrirAsignar(tipo) {
  accionPendiente.value = { tipo: tipo || 'asignar', estado_nuevo: 'ASIGNADA' }
  asignarResponsableId.value = null
  asignarMotivo.value = ''
  dialogAsignar.value = true
}

function confirmarAsignar() {
  if (!asignarResponsableId.value) {
    toast.add({
      severity: 'warn',
      summary: 'Falta responsable',
      detail: 'Seleccioná un responsable.',
    })
    return
  }
  const payload = {
    estado_nuevo: 'ASIGNADA',
    responsable_nuevo: asignarResponsableId.value,
  }
  if (asignarMotivo.value?.trim()) payload.motivo = asignarMotivo.value.trim()
  ejecutarCambioEstado(payload)
}

// Dialog Motivo: para EN_ESPERA y Devolver al sector
function abrirMotivo(tipo) {
  accionPendiente.value = { tipo, estado_nuevo: tipo === 'en_espera' ? 'EN_ESPERA' : 'ARCHIVADA' }
  motivoTexto.value = ''
  dialogMotivo.value = true
}

function confirmarMotivo() {
  const acc = accionPendiente.value
  const motivo = motivoTexto.value?.trim() || ''
  if (!acc) return
  if (motivo.length < 10) {
    toast.add({
      severity: 'warn',
      summary: 'Motivo obligatorio',
      detail: 'El motivo debe tener al menos 10 caracteres.',
    })
    return
  }
  let payload
  if (acc.tipo === 'en_espera') {
    payload = { estado_nuevo: 'EN_ESPERA', motivo }
  } else {
    payload = { estado_nuevo: 'ARCHIVADA', motivo: 'Devuelta al sector: ' + motivo }
  }
  ejecutarCambioEstado(payload)
}

// Acciones directas (sin dialog)
function iniciarProceso() {
  ejecutarCambioEstado({ estado_nuevo: 'EN_PROCESO' })
}

function marcarResuelta() {
  ejecutarCambioEstado({ estado_nuevo: 'RESUELTA' })
}

function retomar() {
  ejecutarCambioEstado({ estado_nuevo: 'EN_PROCESO' })
}

function archivar() {
  ejecutarCambioEstado({ estado_nuevo: 'ARCHIVADA' })
}

onMounted(() => {
  Promise.all([cargarNota(), cargarSectores(), cargarUsuarios()])
})

watch(notaId, (nuevo) => {
  if (nuevo) cargarNota()
})
</script>

<template>
  <div class="nota-detalle min-h-full" style="background-color: #eef2f7">
    <div class="p-4 md:p-6 max-w-6xl mx-auto">
      <!-- Header -->
      <header class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="flex flex-wrap items-center gap-3">
          <Button
            label="Volver a Notas"
            icon="pi pi-arrow-left"
            text
            class="p-0 text-[#1e3a5f] font-medium"
            @click="volverANotas"
          />
          <template v-if="nota">
            <span class="text-2xl md:text-3xl font-mono font-bold text-[#1e3a5f]">
              {{ nota.numero_nota || '—' }}
            </span>
            <Tag
              :value="labelEstado(nota.estado)"
              :style="{
                background: colorEstado(nota.estado),
                color: ['ARCHIVADA', 'ANULADA'].includes(nota.estado) ? 'white' : 'white',
                border: 'none',
              }"
              class="!text-sm"
            />
          </template>
        </div>
      </header>

      <!-- Error -->
      <div
        v-if="error"
        class="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm flex items-center justify-between gap-2"
      >
        <span>{{ error }}</span>
        <Button label="Reintentar" icon="pi pi-refresh" size="small" @click="cargarNota" />
      </div>

      <!-- Loading -->
      <div v-if="cargando" class="flex justify-center py-12">
        <ProgressBar mode="indeterminate" style="height: 4px; width: 100%; max-width: 400px" />
      </div>

      <!-- Contenido en dos columnas -->
      <div v-if="!cargando && nota" class="grid grid-cols-1 lg:grid-cols-10 gap-6">
        <!-- Columna principal (70%) -->
        <div class="lg:col-span-7 space-y-6">
          <!-- Card 1 — Identificación -->
          <Card>
            <template #title>Identificación</template>
            <template #content>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">Número de nota</p>
                  <p class="font-mono text-lg text-[#1e3a5f] font-semibold">
                    {{ nota.numero_nota || '—' }}
                  </p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">Sector de origen</p>
                  <p class="text-gray-800">{{ sectorOrigenDisplay }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">Fecha de ingreso</p>
                  <p class="text-gray-800">{{ formatoFechaHora(nota.fecha_ingreso) }}</p>
                </div>
                <div v-if="nota.canal_ingreso">
                  <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">Canal de ingreso</p>
                  <p class="text-gray-800">{{ labelCanal(nota.canal_ingreso) }}</p>
                </div>
              </div>
            </template>
          </Card>

          <!-- Card 2 — Contenido -->
          <Card>
            <template #title>Contenido</template>
            <template #content>
              <div class="space-y-4">
                <div>
                  <h2 class="text-lg font-semibold text-[#1e3a5f]">{{ nota.tema || '—' }}</h2>
                </div>
                <div v-if="nota.tarea_asignada" class="flex gap-2 items-start">
                  <i class="pi pi-flag text-orange-500 mt-0.5" />
                  <p class="text-gray-700">{{ nota.tarea_asignada }}</p>
                </div>
                <div v-if="nota.descripcion" class="text-gray-700 whitespace-pre-wrap">
                  {{ nota.descripcion }}
                </div>
              </div>
            </template>
          </Card>

          <!-- Card 3 — Historial -->
          <Card>
            <template #title>Historial</template>
            <template #content>
              <div class="space-y-0">
                <div
                  v-for="(ev, index) in historialOrdenado"
                  :key="ev.id"
                  class="flex gap-4 py-3 border-b border-gray-100 last:border-0"
                >
                  <div
                    class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
                    :style="{
                      backgroundColor: colorIconoEvento(ev.tipo_evento) + '20',
                      color: colorIconoEvento(ev.tipo_evento),
                    }"
                  >
                    <i :class="['pi', iconoEvento(ev.tipo_evento)]" class="text-sm" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-xs text-gray-500">{{ formatoFechaHora(ev.fecha_hora) }}</p>
                    <p class="text-sm font-medium text-gray-800">{{ ev.usuario || 'Sistema' }}</p>
                    <p class="text-sm text-gray-600">
                      {{ ev.descripcion_cambio || ev.tipo_evento }}
                    </p>
                  </div>
                </div>
                <p v-if="!historialOrdenado.length" class="text-gray-500 text-sm py-2">
                  Sin registros en el historial.
                </p>
              </div>
            </template>
          </Card>

          <!-- Card 4 — Adjuntos -->
          <Card>
            <template #title>Adjuntos</template>
            <template #content>
              <ul class="space-y-2">
                <li
                  v-for="adj in nota.adjuntos || []"
                  :key="adj.id"
                  class="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg"
                >
                  <div class="min-w-0 flex-1 mr-2">
                    <p class="text-sm font-medium text-gray-800 truncate">
                      {{ adj.nombre_archivo }}
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ adj.tipo_adjunto }} ·
                      {{ adj.tamaño_formateado || adj.tamaño_bytes + ' bytes' }} ·
                      {{ formatoFechaHora(adj.fecha_subida) }}
                    </p>
                  </div>
                  <Button
                    icon="pi pi-download"
                    text
                    rounded
                    size="small"
                    v-tooltip.top="'Descargar'"
                    @click="() => {}"
                  />
                </li>
              </ul>
              <p v-if="!nota.adjuntos?.length" class="text-gray-500 text-sm py-2">
                No hay adjuntos.
              </p>
              <Button
                v-if="esSupervisorOAdmin || esResponsable"
                label="Agregar adjunto"
                icon="pi pi-paperclip"
                class="mt-2"
                severity="secondary"
                @click="() => {}"
              />
            </template>
          </Card>
        </div>

        <!-- Panel lateral (30%) -->
        <div class="lg:col-span-3 space-y-6">
          <!-- Card Estado y responsable -->
          <Card>
            <template #title>Estado y responsable</template>
            <template #content>
              <div class="space-y-4">
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">Estado actual</p>
                  <Tag
                    :value="labelEstado(nota.estado)"
                    :style="{
                      background: colorEstado(nota.estado),
                      color: 'white',
                      border: 'none',
                    }"
                    class="!text-sm"
                  />
                </div>
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">Responsable</p>
                  <div class="flex items-center gap-2">
                    <div
                      class="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm"
                      style="background-color: #1e3a5f"
                    >
                      {{ responsableIniciales }}
                    </div>
                    <span class="text-gray-800">{{
                      nota.responsable?.nombre_completo || 'Sin asignar'
                    }}</span>
                  </div>
                </div>
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">
                    Última modificación
                  </p>
                  <p class="text-gray-700 text-sm">
                    {{ formatoFechaHora(nota.ultima_modificacion) }}
                  </p>
                </div>
              </div>
            </template>
          </Card>

          <!-- Card Acciones disponibles: lógica por estado con v-if separados para responsable y supervisor -->
          <Card>
            <template #title>Acciones disponibles</template>
            <template #content>
              <div v-if="nota.estado === 'ARCHIVADA'" class="text-gray-600 text-sm py-2">
                Esta nota está archivada
              </div>
              <div v-else class="flex flex-col gap-2">
                <!-- INGRESADA: solo supervisor/admin -->
                <template v-if="nota.estado === 'INGRESADA'">
                  <template v-if="esSupervisorOAdmin">
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#1e3a5f] hover:bg-[#2d4f7c] transition-colors"
                      :disabled="enviandoAccion"
                      @click="abrirAsignar('asignar')"
                    >
                      Asignar
                    </button>
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#64748b] hover:bg-[#475569] transition-colors"
                      :disabled="enviandoAccion"
                      @click="archivar"
                    >
                      Archivar
                    </button>
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#f97316] hover:bg-[#ea580c] transition-colors"
                      :disabled="enviandoAccion"
                      @click="abrirMotivo('devolver')"
                    >
                      Devolver al sector
                    </button>
                  </template>
                </template>

                <!-- ASIGNADA: responsable → Iniciar proceso; supervisor → Reasignar, Archivar, Devolver -->
                <template v-if="nota.estado === 'ASIGNADA'">
                  <button
                    v-if="esResponsable"
                    type="button"
                    class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#1e3a5f] hover:bg-[#2d4f7c] transition-colors"
                    :disabled="enviandoAccion"
                    @click="iniciarProceso"
                  >
                    Iniciar proceso
                  </button>
                  <template v-if="esSupervisorOAdmin">
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#64748b] hover:bg-[#475569] transition-colors"
                      :disabled="enviandoAccion"
                      @click="abrirAsignar('reasignar')"
                    >
                      Reasignar
                    </button>
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#64748b] hover:bg-[#475569] transition-colors"
                      :disabled="enviandoAccion"
                      @click="archivar"
                    >
                      Archivar
                    </button>
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#f97316] hover:bg-[#ea580c] transition-colors"
                      :disabled="enviandoAccion"
                      @click="abrirMotivo('devolver')"
                    >
                      Devolver al sector
                    </button>
                  </template>
                </template>

                <!-- EN_PROCESO: responsable → Marcar resuelta, Poner en espera; supervisor → Reasignar, Archivar, Devolver -->
                <template v-if="nota.estado === 'EN_PROCESO'">
                  <template v-if="esResponsable">
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#059669] hover:bg-[#047857] transition-colors"
                      :disabled="enviandoAccion"
                      @click="marcarResuelta"
                    >
                      Marcar como resuelta
                    </button>
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#d97706] hover:bg-[#b45309] transition-colors"
                      :disabled="enviandoAccion"
                      @click="abrirMotivo('en_espera')"
                    >
                      Poner en espera
                    </button>
                  </template>
                  <template v-if="esSupervisorOAdmin">
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#64748b] hover:bg-[#475569] transition-colors"
                      :disabled="enviandoAccion"
                      @click="abrirAsignar('reasignar')"
                    >
                      Reasignar
                    </button>
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#64748b] hover:bg-[#475569] transition-colors"
                      :disabled="enviandoAccion"
                      @click="archivar"
                    >
                      Archivar
                    </button>
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#f97316] hover:bg-[#ea580c] transition-colors"
                      :disabled="enviandoAccion"
                      @click="abrirMotivo('devolver')"
                    >
                      Devolver al sector
                    </button>
                  </template>
                </template>

                <!-- EN_ESPERA: responsable → Retomar; supervisor → Reasignar, Archivar, Devolver -->
                <template v-if="nota.estado === 'EN_ESPERA'">
                  <button
                    v-if="esResponsable"
                    type="button"
                    class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#1e3a5f] hover:bg-[#2d4f7c] transition-colors"
                    :disabled="enviandoAccion"
                    @click="retomar"
                  >
                    Retomar
                  </button>
                  <template v-if="esSupervisorOAdmin">
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#64748b] hover:bg-[#475569] transition-colors"
                      :disabled="enviandoAccion"
                      @click="abrirAsignar('reasignar')"
                    >
                      Reasignar
                    </button>
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#64748b] hover:bg-[#475569] transition-colors"
                      :disabled="enviandoAccion"
                      @click="archivar"
                    >
                      Archivar
                    </button>
                    <button
                      type="button"
                      class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#f97316] hover:bg-[#ea580c] transition-colors"
                      :disabled="enviandoAccion"
                      @click="abrirMotivo('devolver')"
                    >
                      Devolver al sector
                    </button>
                  </template>
                </template>

                <!-- RESUELTA: Archivar si responsable o supervisor -->
                <template
                  v-if="nota.estado === 'RESUELTA' && (esResponsable || esSupervisorOAdmin)"
                >
                  <button
                    type="button"
                    class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#065f46] hover:bg-[#064e3b] transition-colors"
                    :disabled="enviandoAccion"
                    @click="archivar"
                  >
                    Archivar
                  </button>
                </template>
              </div>
            </template>
          </Card>

          <!-- Card Información adicional -->
          <Card>
            <template #title>Información adicional</template>
            <template #content>
              <div class="space-y-3">
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">Prioridad</p>
                  <Tag
                    :value="labelPrioridad(nota.prioridad)"
                    :style="{
                      background: colorPrioridad(nota.prioridad),
                      color: ['BAJA', 'MEDIA', 'NORMAL'].includes(nota.prioridad)
                        ? '#1e293b'
                        : 'white',
                      border: 'none',
                    }"
                    class="!text-xs"
                  />
                </div>
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">Creado por</p>
                  <p class="text-sm text-gray-800">{{ nota.creado_por || '—' }}</p>
                  <p class="text-xs text-gray-500">{{ formatoFechaHora(nota.fecha_creacion) }}</p>
                </div>
                <template v-if="nota.genera_resolucion">
                  <div v-if="nota.numero_resolucion">
                    <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Número de resolución
                    </p>
                    <p class="text-sm text-gray-800">{{ nota.numero_resolucion }}</p>
                  </div>
                  <div v-if="nota.fecha_resolucion">
                    <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">
                      Fecha de resolución
                    </p>
                    <p class="text-sm text-gray-800">{{ formatoFecha(nota.fecha_resolucion) }}</p>
                  </div>
                </template>
              </div>
            </template>
          </Card>
        </div>
      </div>
    </div>

    <!-- Dialog Asignar / Reasignar -->
    <Dialog
      v-model:visible="dialogAsignar"
      :header="accionPendiente?.tipo === 'reasignar' ? 'Reasignar nota' : 'Asignar nota'"
      :modal="true"
      :closable="true"
      :style="{ width: '400px' }"
      @hide="cerrarDialogs"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Responsable</label>
          <Dropdown
            v-model="asignarResponsableId"
            :options="usuariosParaAsignar"
            option-label="nombre_completo"
            option-value="id"
            placeholder="Seleccionar responsable"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Motivo (opcional)</label>
          <Textarea
            v-model="asignarMotivo"
            rows="2"
            class="w-full"
            placeholder="Motivo de la asignación"
          />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="cerrarDialogs" />
        <Button
          label="Confirmar"
          icon="pi pi-check"
          :loading="enviandoAccion"
          @click="confirmarAsignar"
        />
      </template>
    </Dialog>

    <!-- Dialog Motivo (EN_ESPERA, Devolver al sector) -->
    <Dialog
      v-model:visible="dialogMotivo"
      :header="accionPendiente?.tipo === 'en_espera' ? 'Motivo de la espera' : 'Devolver al sector'"
      :modal="true"
      :closable="true"
      :style="{ width: '400px' }"
      @hide="cerrarDialogs"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >Motivo (obligatorio, mínimo 10 caracteres)</label
          >
          <Textarea
            v-model="motivoTexto"
            rows="3"
            class="w-full"
            placeholder="Describa el motivo"
          />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="cerrarDialogs" />
        <Button
          label="Confirmar"
          icon="pi pi-check"
          :loading="enviandoAccion"
          @click="confirmarMotivo"
        />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.nota-detalle {
  min-height: 100%;
}

.nota-detalle :deep(.p-card) {
  background-color: white !important;
  color: #1e293b !important;
}

.nota-detalle :deep(.p-card-title) {
  color: #1e3a5f !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
}

.nota-detalle :deep(.p-dialog) {
  background-color: white !important;
}

.nota-detalle :deep(.p-dialog-header) {
  background-color: white !important;
  color: #1e3a5f !important;
}

.nota-detalle :deep(.p-dialog-content) {
  background-color: white !important;
}

.nota-detalle :deep(.p-select),
.nota-detalle :deep(.p-inputtext),
.nota-detalle :deep(.p-textarea) {
  background-color: white !important;
  color: #1e293b !important;
  border: 1px solid #e2e8f0 !important;
}

.nota-detalle :deep(.p-select-overlay) {
  background-color: white !important;
}

.nota-detalle :deep(.p-select-option) {
  color: #1e293b !important;
  background-color: white !important;
}

.nota-detalle :deep(.p-select-option:hover) {
  background-color: #f1f5f9 !important;
}
</style>
