<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { notasService, sectoresService, usuariosService } from '@/services/notasService'
import { useToast } from '@/composables/useToast'
import { usePermisos } from '@/composables/usePermisos'
import BtnVolver from '@/components/BtnVolver.vue'
import { formatoFecha, formatoFechaHora, accionesDisponibles, toArray } from '@/utils/notas'
import BadgeEstado from '@/components/BadgeEstado.vue'
import BadgePrioridad from '@/components/BadgePrioridad.vue'

const route = useRoute()

const {
  mensajeExito,
  mostrarExito,
  mensajeError,
  mostrarError,
  mostrarToastExito,
  mostrarToastError,
} = useToast()

// Estado
const nota = ref(null)
const sectores = ref([])
const usuarios = ref([])
const cargando = ref(true)
const error = ref(null)
const enviandoAccion = ref(false)
const inputArchivo = ref(null)
const subiendoAdjunto = ref(false)

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

const { esSupervisorOAdmin, rol, usuarioId, esResponsableDe } = usePermisos()

const esResponsable = computed(() => esResponsableDe(nota.value))

const acciones = computed(() => {
  if (!nota.value) return { habilitadas: [], deshabilitadas: [] }
  return accionesDisponibles(nota.value.estado, rol.value, esResponsable.value)
})

const puedeHacer = (accion) => acciones.value.habilitadas.includes(accion)

const motivoDeshabilitado = (accion) =>
  acciones.value.deshabilitadas.find((d) => d.accion === accion)?.motivo

/** Deshabilitado solo si figura en deshabilitadas y no está habilitada (habilitadas gana). */
const estaDeshabilitado = (accion) => {
  if (puedeHacer(accion)) return false
  return !!acciones.value.deshabilitadas.find((d) => d.accion === accion)
}

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
    nota.value = await notasService.getNota(notaId.value)
  } catch (e) {
    error.value = e.data?.detalle || e.data?.error || e.message || 'Error al cargar la nota.'
    nota.value = null
  } finally {
    cargando.value = false
  }
}

async function cargarSectores() {
  try {
    const res = await sectoresService.getSectores('?activos=true')
    sectores.value = toArray(res)
  } catch {
    sectores.value = []
  }
}

async function cargarUsuarios() {
  try {
    const res = await usuariosService.getUsuariosActivos()
    usuarios.value = toArray(res)
  } catch {
    usuarios.value = []
  }
}

async function subirAdjunto(event) {
  const archivo = event.target.files[0]
  if (!archivo) return

  subiendoAdjunto.value = true
  try {
    const formData = new FormData()
    formData.append('archivo', archivo)
    formData.append('nombre_archivo', archivo.name)
    formData.append('tipo_adjunto', 'DOCUMENTO_ORIGINAL')

    await notasService.subirAdjunto(nota.value.id, formData)

    mostrarToastExito('Adjunto subido correctamente')
    await cargarNota()
  } catch (error) {
    mostrarToastError(
      error?.data?.detail || error?.data?.detalle || error?.message || 'Error al subir el adjunto',
    )
  } finally {
    subiendoAdjunto.value = false
    event.target.value = ''
  }
}

// Cambio de estado
async function ejecutarCambioEstado(payload) {
  enviandoAccion.value = true
  try {
    await notasService.cambiarEstado(notaId.value, payload)
    mostrarToastExito('Estado actualizado correctamente')
    await cargarNota()
    cerrarDialogs()
  } catch (e) {
    const msg = e.data?.detalle || e.data?.error || e.message || 'Error al cambiar el estado.'
    mostrarToastError(msg)
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
    mostrarToastError('Seleccioná un responsable.')
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
    mostrarToastError('El motivo debe tener al menos 10 caracteres.')
    return
  }
  let payload
  if (acc.tipo === 'en_espera') {
    payload = { estado_nuevo: 'EN_ESPERA', motivo }
  } else {
    payload = { estado_nuevo: 'ARCHIVADA', motivo: 'Devuelta: ' + motivo }
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

function accionIniciar() {
  iniciarProceso()
}
function accionResuelta() {
  marcarResuelta()
}
function accionEnEspera() {
  abrirMotivo('en_espera')
}
function accionRetomar() {
  retomar()
}
function abrirModalAsignar() {
  abrirAsignar('asignar')
}
function abrirModalReasignar() {
  abrirAsignar('reasignar')
}
function accionDevuelta() {
  abrirMotivo('devolver')
}

// Autoasignarse: solo SUPERVISOR/ADMIN cuando INGRESADA sin responsable o ASIGNADA a otro
const puedeAutoasignarse = computed(() => {
  if (!esSupervisorOAdmin.value || !nota.value) return false
  if (nota.value.estado === 'INGRESADA') {
    const sinResponsable = !nota.value.responsable || !nota.value.responsable.id
    return !!sinResponsable
  }
  if (nota.value.estado === 'ASIGNADA') return !esResponsable.value
  return false
})

async function autoasignarse() {
  if (usuarioId.value == null) return
  enviandoAccion.value = true
  try {
    await notasService.cambiarEstado(notaId.value, {
      estado_nuevo: 'ASIGNADA',
      responsable_nuevo: usuarioId.value,
    })
    mostrarToastExito('Estado actualizado correctamente')
    await cargarNota()
  } catch (e) {
    const msg = e.data?.detalle || e.data?.error || e.message || 'Error al autoasignarse.'
    mostrarToastError(msg)
  } finally {
    enviandoAccion.value = false
  }
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
    <!-- Toast éxito -->
    <Transition name="slide-down">
      <div
        v-if="mostrarExito"
        class="fixed top-4 right-4 z-[9999] flex items-center gap-3 bg-[#059669] text-white px-5 py-3 rounded-lg shadow-lg"
      >
        <i class="pi pi-check-circle text-lg" />
        <span class="font-medium">{{ mensajeExito }}</span>
      </div>
    </Transition>

    <!-- Toast error -->
    <Transition name="slide-down">
      <div
        v-if="mostrarError"
        class="fixed top-4 right-4 z-[9999] flex items-center gap-3 bg-[#dc2626] text-white px-5 py-3 rounded-lg shadow-lg"
      >
        <i class="pi pi-times-circle text-lg" />
        <span class="font-medium">{{ mensajeError }}</span>
      </div>
    </Transition>

    <div class="p-4 md:p-6 max-w-6xl mx-auto">
      <!-- Header -->
      <header class="mb-6">
        <!-- Back navigation -->
        <div class="mb-3">
          <BtnVolver label="Volver" />
        </div>

        <!-- Título principal -->
        <div v-if="nota" class="flex flex-wrap items-center gap-3">
          <span class="text-2xl md:text-3xl font-mono font-bold text-[#1e3a5f]">
            {{ nota.numero_nota || '—' }}
          </span>
          <BadgeEstado :estado="nota.estado" />
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
        <!-- Columna principal (70%) — 4 cards verticales -->
        <div class="lg:col-span-7 space-y-6">
          <!-- Card 1: Identificación -->
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
                <div v-if="nota.email_respuesta">
                  <p class="text-xs text-gray-600 uppercase tracking-wide mb-1">
                    Email de respuesta
                  </p>
                  <p class="text-sm text-gray-800 flex items-center gap-1">
                    <i class="pi pi-envelope text-xs text-gray-600" />
                    {{ nota.email_respuesta }}
                  </p>
                </div>
              </div>
            </template>
          </Card>

          <!-- Card 2: Contenido -->
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

          <!-- Card 3: Adjuntos -->
          <Card>
            <template #title>Adjuntos</template>
            <template #content>
              <input
                ref="inputArchivo"
                type="file"
                class="hidden"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
                @change="subirAdjunto"
              />
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
                  <div class="flex items-center gap-1">
                    <!-- Ver archivo -->
                    <a
                      v-if="adj?.url"
                      :href="adj.url"
                      target="_blank"
                      v-tooltip.top="'Ver'"
                      class="inline-flex items-center justify-center w-8 h-8 rounded-full text-[#1e3a5f] hover:bg-gray-100 transition-colors cursor-pointer"
                    >
                      <i class="pi pi-eye text-sm" />
                    </a>
                    <!-- Descargar archivo -->
                    <a
                      v-if="adj?.url"
                      :href="adj.url"
                      :download="adj.nombre_archivo"
                      v-tooltip.top="'Descargar'"
                      class="inline-flex items-center justify-center w-8 h-8 rounded-full text-[#1e3a5f] hover:bg-gray-100 transition-colors cursor-pointer"
                    >
                      <i class="pi pi-download text-sm" />
                    </a>
                  </div>
                </li>
              </ul>
              <p v-if="!nota.adjuntos?.length" class="text-gray-500 text-sm py-2">
                No hay adjuntos.
              </p>
            </template>
          </Card>

          <!-- Card 4: Historial -->
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
                  <BadgeEstado :estado="nota.estado" />
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

          <!-- Card Acciones disponibles (accionesDisponibles en utils/notas.js) -->
          <Card>
            <template #title>Acciones disponibles</template>
            <template #content>
              <div v-if="nota.estado === 'ARCHIVADA'" class="text-gray-600 text-sm py-2">
                Esta nota está archivada
              </div>
              <div v-else class="flex flex-col gap-2">
                <button
                  v-if="puedeAutoasignarse"
                  type="button"
                  class="w-full py-2 px-4 rounded-lg text-white font-medium bg-[#0891b2] hover:bg-[#0e7490] transition-colors"
                  :disabled="enviandoAccion"
                  @click="autoasignarse"
                >
                  Autoasignarse
                </button>

                <button
                  v-if="puedeHacer('asignar') || estaDeshabilitado('asignar')"
                  type="button"
                  :disabled="estaDeshabilitado('asignar') || enviandoAccion"
                  v-tooltip.left="motivoDeshabilitado('asignar')"
                  class="w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors"
                  :class="
                    puedeHacer('asignar')
                      ? 'bg-[#6366f1] text-white hover:bg-[#4f46e5] cursor-pointer'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  "
                  @click="puedeHacer('asignar') && abrirModalAsignar()"
                >
                  Asignar
                </button>

                <button
                  v-if="puedeHacer('iniciar') || estaDeshabilitado('iniciar')"
                  type="button"
                  :disabled="estaDeshabilitado('iniciar') || enviandoAccion"
                  v-tooltip.left="motivoDeshabilitado('iniciar')"
                  class="w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors"
                  :class="
                    puedeHacer('iniciar')
                      ? 'bg-[#1e3a5f] text-white hover:bg-[#162d4a] cursor-pointer'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  "
                  @click="puedeHacer('iniciar') && accionIniciar()"
                >
                  Iniciar proceso
                </button>

                <button
                  v-if="puedeHacer('resuelta') || estaDeshabilitado('resuelta')"
                  type="button"
                  :disabled="estaDeshabilitado('resuelta') || enviandoAccion"
                  v-tooltip.left="motivoDeshabilitado('resuelta')"
                  class="w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors"
                  :class="
                    puedeHacer('resuelta')
                      ? 'bg-[#059669] text-white hover:bg-[#047857] cursor-pointer'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  "
                  @click="puedeHacer('resuelta') && accionResuelta()"
                >
                  Resuelta
                </button>

                <button
                  v-if="puedeHacer('en_espera') || estaDeshabilitado('en_espera')"
                  type="button"
                  :disabled="estaDeshabilitado('en_espera') || enviandoAccion"
                  v-tooltip.left="motivoDeshabilitado('en_espera')"
                  class="w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors"
                  :class="
                    puedeHacer('en_espera')
                      ? 'bg-[#d97706] text-white hover:bg-[#b45309] cursor-pointer'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  "
                  @click="puedeHacer('en_espera') && accionEnEspera()"
                >
                  En espera
                </button>

                <button
                  v-if="puedeHacer('retomar') || estaDeshabilitado('retomar')"
                  type="button"
                  :disabled="estaDeshabilitado('retomar') || enviandoAccion"
                  v-tooltip.left="motivoDeshabilitado('retomar')"
                  class="w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors"
                  :class="
                    puedeHacer('retomar')
                      ? 'bg-[#1e3a5f] text-white hover:bg-[#162d4a] cursor-pointer'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  "
                  @click="puedeHacer('retomar') && accionRetomar()"
                >
                  Retomar
                </button>

                <button
                  v-if="puedeHacer('reasignar') || estaDeshabilitado('reasignar')"
                  type="button"
                  :disabled="estaDeshabilitado('reasignar') || enviandoAccion"
                  v-tooltip.left="motivoDeshabilitado('reasignar')"
                  class="w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors"
                  :class="
                    puedeHacer('reasignar')
                      ? 'bg-[#475569] text-white hover:bg-[#334155] cursor-pointer'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  "
                  @click="puedeHacer('reasignar') && abrirModalReasignar()"
                >
                  Reasignar
                </button>

                <button
                  v-if="puedeHacer('devuelta') || estaDeshabilitado('devuelta')"
                  type="button"
                  :disabled="estaDeshabilitado('devuelta') || enviandoAccion"
                  v-tooltip.left="motivoDeshabilitado('devuelta')"
                  class="w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors"
                  :class="
                    puedeHacer('devuelta')
                      ? 'bg-[#f97316] text-white hover:bg-[#ea580c] cursor-pointer'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  "
                  @click="puedeHacer('devuelta') && accionDevuelta()"
                >
                  Devolver
                </button>

                <button
                  v-if="puedeHacer('archivar') || estaDeshabilitado('archivar')"
                  type="button"
                  :disabled="estaDeshabilitado('archivar') || enviandoAccion"
                  v-tooltip.left="motivoDeshabilitado('archivar')"
                  class="w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors"
                  :class="
                    puedeHacer('archivar')
                      ? 'bg-[#64748b] text-white hover:bg-[#475569] cursor-pointer'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  "
                  @click="puedeHacer('archivar') && archivar()"
                >
                  Archivar
                </button>
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
                  <BadgePrioridad :prioridad="nota.prioridad" />
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
      :header="accionPendiente?.tipo === 'en_espera' ? 'Motivo de la espera' : 'Devolver'"
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
</style>
