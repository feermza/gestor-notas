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
const dialogAnular = ref(false)

// Formularios de dialogs
const asignarResponsableId = ref(null)
const asignarMotivo = ref('')
const motivoTexto = ref('')
const motivoResponsableId = ref(null) // para DEVUELTA
const accionPendiente = ref(null) // { estado_nuevo, requiereResponsable, requiereMotivo }

// Opciones para dropdowns
const opcionesUsuarios = computed(() =>
  usuarios.value
    .filter((u) => u.rol !== 'CONSULTOR')
    .map((u) => ({
      value: u.id,
      label: `${u.nombre_completo} (${u.rol_display || u.rol})`,
    }))
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
const rol = computed(() => usuarioActual.value?.rol ?? null)
const esResponsable = computed(() => {
  if (!nota.value || !usuarioActual.value) return false
  const responsableId = nota.value.responsable_id ?? (typeof nota.value.responsable === 'object' ? nota.value.responsable?.id : null)
  if (responsableId) return usuarioActual.value.id === responsableId
  // Si la API solo devuelve responsable como string (nombre_completo), comparar por nombre
  const respStr = (nota.value.responsable || '').trim()
  const miNombre = (usuarioActual.value.nombre_completo || '').trim()
  return respStr && miNombre && respStr === miNombre
})
const puedeSupervisorOAdmin = computed(() =>
  rol.value === 'SUPERVISOR' || rol.value === 'ADMINISTRADOR'
)

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
    toast.add({ severity: 'success', summary: 'Estado actualizado', detail: 'La nota se actualizó correctamente.' })
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
  dialogAnular.value = false
  accionPendiente.value = null
  asignarResponsableId.value = null
  asignarMotivo.value = ''
  motivoTexto.value = ''
  motivoResponsableId.value = null
}

function abrirAsignar() {
  accionPendiente.value = { estado_nuevo: 'ASIGNADA', requiereResponsable: true, requiereMotivo: false }
  asignarResponsableId.value = null
  asignarMotivo.value = ''
  dialogAsignar.value = true
}

function confirmarAsignar() {
  if (!asignarResponsableId.value) {
    toast.add({ severity: 'warn', summary: 'Falta responsable', detail: 'Seleccioná un responsable.' })
    return
  }
  ejecutarCambioEstado({
    estado_nuevo: 'ASIGNADA',
    responsable_nuevo: asignarResponsableId.value,
    motivo: asignarMotivo.value || undefined,
  })
}

function abrirMotivo(estadoNuevo, requiereResponsable = false) {
  accionPendiente.value = {
    estado_nuevo: estadoNuevo,
    requiereResponsable,
    requiereMotivo: true,
  }
  motivoTexto.value = ''
  motivoResponsableId.value = null
  dialogMotivo.value = true
}

function confirmarMotivo() {
  const acc = accionPendiente.value
  if (!acc || !motivoTexto.value.trim()) {
    toast.add({ severity: 'warn', summary: 'Motivo obligatorio', detail: 'Ingresá el motivo.' })
    return
  }
  if (acc.requiereResponsable && !motivoResponsableId.value) {
    toast.add({ severity: 'warn', summary: 'Falta responsable', detail: 'Seleccioná el nuevo responsable.' })
    return
  }
  const payload = {
    estado_nuevo: acc.estado_nuevo,
    motivo: motivoTexto.value.trim(),
  }
  if (acc.requiereResponsable) payload.responsable_nuevo = motivoResponsableId.value
  ejecutarCambioEstado(payload)
}

function abrirAnular() {
  accionPendiente.value = { estado_nuevo: 'ANULADA', requiereMotivo: true }
  motivoTexto.value = ''
  dialogAnular.value = true
}

function confirmarAnular() {
  if (!motivoTexto.value.trim()) {
    toast.add({ severity: 'warn', summary: 'Motivo obligatorio', detail: 'Ingresá el motivo de anulación.' })
    return
  }
  ejecutarCambioEstado({
    estado_nuevo: 'ANULADA',
    motivo: motivoTexto.value.trim(),
  })
}

// Acciones directas (sin dialog)
function ponerEnRevision() {
  ejecutarCambioEstado({ estado_nuevo: 'EN_REVISION' })
}

function iniciarProceso() {
  ejecutarCambioEstado({ estado_nuevo: 'EN_PROCESO' })
}

function marcarResuelta() {
  ejecutarCambioEstado({ estado_nuevo: 'RESUELTA' })
}

function archivar() {
  ejecutarCambioEstado({ estado_nuevo: 'ARCHIVADA' })
}

// Botones de acciones disponibles
const accionesDisponibles = computed(() => {
  const n = nota.value
  const estado = n?.estado
  const acciones = []

  if (estado === 'INGRESADA' && puedeSupervisorOAdmin.value) {
    acciones.push({ label: 'Poner en Revisión', icon: 'pi-arrow-right', handler: ponerEnRevision, estado_nuevo: 'EN_REVISION' })
  }

  if (estado === 'EN_REVISION' && puedeSupervisorOAdmin.value) {
    acciones.push({ label: 'Asignar', icon: 'pi-user-plus', dialog: 'asignar' })
  }

  if (estado === 'ASIGNADA' && (esResponsable.value || puedeSupervisorOAdmin.value)) {
    acciones.push({ label: 'Iniciar proceso', icon: 'pi-play', handler: iniciarProceso, estado_nuevo: 'EN_PROCESO' })
  }

  if (estado === 'EN_PROCESO' && (esResponsable.value || puedeSupervisorOAdmin.value)) {
    acciones.push({ label: 'Marcar como resuelta', icon: 'pi-check', handler: marcarResuelta, estado_nuevo: 'RESUELTA' })
    acciones.push({ label: 'Poner en espera', icon: 'pi-clock', dialog: 'motivo', estado_nuevo: 'EN_ESPERA' })
    acciones.push({ label: 'Devolver', icon: 'pi-replay', dialog: 'motivo-devolver', estado_nuevo: 'DEVUELTA' })
  }

  if (estado === 'RESUELTA' && (esResponsable.value || puedeSupervisorOAdmin.value)) {
    acciones.push({ label: 'Archivar', icon: 'pi-archive', handler: archivar, estado_nuevo: 'ARCHIVADA' })
  }

  if (estado && estado !== 'ANULADA' && estado !== 'ARCHIVADA' && puedeSupervisorOAdmin.value) {
    acciones.push({ label: 'Anular', icon: 'pi-times-circle', dialog: 'anular', severity: 'danger', estado_nuevo: 'ANULADA' })
  }

  return acciones
})

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
                  <p class="font-mono text-lg text-[#1e3a5f] font-semibold">{{ nota.numero_nota || '—' }}</p>
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
                <div v-if="nota.descripcion" class="text-gray-700 whitespace-pre-wrap">{{ nota.descripcion }}</div>
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
                    :style="{ backgroundColor: colorIconoEvento(ev.tipo_evento) + '20', color: colorIconoEvento(ev.tipo_evento) }"
                  >
                    <i :class="['pi', iconoEvento(ev.tipo_evento)]" class="text-sm" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-xs text-gray-500">{{ formatoFechaHora(ev.fecha_hora) }}</p>
                    <p class="text-sm font-medium text-gray-800">{{ ev.usuario || 'Sistema' }}</p>
                    <p class="text-sm text-gray-600">{{ ev.descripcion_cambio || ev.tipo_evento }}</p>
                  </div>
                </div>
                <p v-if="!historialOrdenado.length" class="text-gray-500 text-sm py-2">Sin registros en el historial.</p>
              </div>
            </template>
          </Card>

          <!-- Card 4 — Adjuntos -->
          <Card>
            <template #title>Adjuntos</template>
            <template #content>
              <ul class="space-y-2">
                <li
                  v-for="adj in (nota.adjuntos || [])"
                  :key="adj.id"
                  class="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg"
                >
                  <div class="min-w-0 flex-1 mr-2">
                    <p class="text-sm font-medium text-gray-800 truncate">{{ adj.nombre_archivo }}</p>
                    <p class="text-xs text-gray-500">
                      {{ adj.tipo_adjunto }} · {{ adj.tamaño_formateado || adj.tamaño_bytes + ' bytes' }} · {{ formatoFechaHora(adj.fecha_subida) }}
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
              <p v-if="!nota.adjuntos?.length" class="text-gray-500 text-sm py-2">No hay adjuntos.</p>
              <Button
                v-if="puedeSupervisorOAdmin || esResponsable"
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
                    <span class="text-gray-800">{{ nota.responsable || 'Sin asignar' }}</span>
                  </div>
                </div>
                <div>
                  <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">Última modificación</p>
                  <p class="text-gray-700 text-sm">{{ formatoFechaHora(nota.ultima_modificacion) }}</p>
                </div>
              </div>
            </template>
          </Card>

          <!-- Card Acciones disponibles -->
          <Card>
            <template #title>Acciones disponibles</template>
            <template #content>
              <div class="flex flex-col gap-2">
                <template v-for="(acc, i) in accionesDisponibles" :key="i">
                  <Button
                    v-if="acc.handler"
                    :label="acc.label"
                    :icon="'pi ' + acc.icon"
                    class="w-full justify-start"
                    :severity="acc.severity === 'danger' ? 'danger' : 'secondary'"
                    :loading="enviandoAccion"
                    @click="acc.handler"
                  />
                  <template v-else>
                    <Button
                      v-if="acc.dialog === 'asignar'"
                      label="Asignar"
                      icon="pi pi-user-plus"
                      class="w-full justify-start"
                      severity="secondary"
                      @click="abrirAsignar"
                    />
                    <Button
                      v-else-if="acc.dialog === 'motivo'"
                      :label="acc.label"
                      :icon="'pi ' + acc.icon"
                      class="w-full justify-start"
                      severity="secondary"
                      @click="abrirMotivo(acc.estado_nuevo, false)"
                    />
                    <Button
                      v-else-if="acc.dialog === 'motivo-devolver'"
                      label="Devolver"
                      icon="pi pi-replay"
                      class="w-full justify-start"
                      severity="secondary"
                      @click="abrirMotivo('DEVUELTA', true)"
                    />
                    <Button
                      v-else-if="acc.dialog === 'anular'"
                      label="Anular"
                      icon="pi pi-times-circle"
                      class="w-full justify-start"
                      severity="danger"
                      @click="abrirAnular"
                    />
                  </template>
                </template>
                <p v-if="!accionesDisponibles.length" class="text-gray-500 text-sm">No hay acciones disponibles.</p>
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
                      color: ['BAJA', 'MEDIA', 'NORMAL'].includes(nota.prioridad) ? '#1e293b' : 'white',
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
                    <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">Número de resolución</p>
                    <p class="text-sm text-gray-800">{{ nota.numero_resolucion }}</p>
                  </div>
                  <div v-if="nota.fecha_resolucion">
                    <p class="text-xs text-gray-500 uppercase tracking-wide mb-1">Fecha de resolución</p>
                    <p class="text-sm text-gray-800">{{ formatoFecha(nota.fecha_resolucion) }}</p>
                  </div>
                </template>
              </div>
            </template>
          </Card>
        </div>
      </div>
    </div>

    <!-- Dialog Asignar responsable -->
    <Dialog
      v-model:visible="dialogAsignar"
      header="Asignar responsable"
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
            :options="opcionesUsuarios"
            option-label="label"
            option-value="value"
            placeholder="Seleccionar responsable"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Motivo (opcional)</label>
          <Textarea v-model="asignarMotivo" rows="2" class="w-full" placeholder="Motivo de la asignación" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="cerrarDialogs" />
        <Button label="Confirmar" icon="pi pi-check" :loading="enviandoAccion" @click="confirmarAsignar" />
      </template>
    </Dialog>

    <!-- Dialog Motivo (EN_ESPERA, DEVUELTA, etc.) -->
    <Dialog
      v-model:visible="dialogMotivo"
      :header="accionPendiente?.estado_nuevo === 'DEVUELTA' ? 'Devolver nota' : 'Ingresar motivo'"
      :modal="true"
      :closable="true"
      :style="{ width: '400px' }"
      @hide="cerrarDialogs"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Motivo (obligatorio)</label>
          <Textarea v-model="motivoTexto" rows="3" class="w-full" placeholder="Describa el motivo" />
        </div>
        <div v-if="accionPendiente?.requiereResponsable">
          <label class="block text-sm font-medium text-gray-700 mb-1">Nuevo responsable</label>
          <Dropdown
            v-model="motivoResponsableId"
            :options="opcionesUsuarios"
            option-label="label"
            option-value="value"
            placeholder="Seleccionar responsable"
            class="w-full"
          />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="cerrarDialogs" />
        <Button label="Confirmar" icon="pi pi-check" :loading="enviandoAccion" @click="confirmarMotivo" />
      </template>
    </Dialog>

    <!-- Dialog Anular -->
    <Dialog
      v-model:visible="dialogAnular"
      header="Anular nota"
      :modal="true"
      :closable="true"
      :style="{ width: '400px' }"
      @hide="cerrarDialogs"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Motivo de anulación (obligatorio)</label>
          <Textarea v-model="motivoTexto" rows="3" class="w-full" placeholder="Indique el motivo de anulación" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="cerrarDialogs" />
        <Button label="Confirmar anulación" icon="pi pi-times" severity="danger" :loading="enviandoAccion" @click="confirmarAnular" />
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
