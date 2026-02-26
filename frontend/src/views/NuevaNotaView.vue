<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { get, post, postFormData } from '@/api/cliente'
import { COLORES_PRIORIDAD, LABELS_PRIORIDAD } from '@/utils/notas'

const router = useRouter()
const toast = useToast()

// Sectores para el dropdown
const sectores = ref([])
const cargandoSectores = ref(true)

// Formulario
const enviando = ref(false)
const errorGeneral = ref(null)

const form = ref({
  canal_ingreso: null,
  sector_origen: null,
  numero_nota_externo: '',
  fecha_ingreso: null,
  fecha_limite: null,
  tema: '',
  descripcion: '',
  prioridad: 'MEDIA',
  emisor_externo: '',
  genera_resolucion: false,
})

// Errores por campo (clave = nombre del campo)
const errores = ref({})

// Adjuntos: lista de { file, tipo_adjunto, nombre_archivo }
const adjuntos = ref([])
const tipoAdjuntoNuevo = ref('DOCUMENTO_ORIGINAL')
const dropZoneActive = ref(false)
const fileInputRef = ref(null)

const MAX_TEMA = 100
const MAX_FILE_MB = 10
const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']

// Opciones de canal (backend: PRESENCIAL, EMAIL, TELEFONO, OTRO)
const opcionesCanal = [
  { value: 'PRESENCIAL', label: 'Papel' },
  { value: 'EMAIL', label: 'Email' },
  { value: 'TELEFONO', label: 'WhatsApp' },
  { value: 'OTRO', label: 'Otro' },
]

const opcionesTipoAdjunto = [
  { value: 'DOCUMENTO_ORIGINAL', label: 'Documento Original' },
  { value: 'OTRO', label: 'Otro' },
]

// Prioridad: opciones con color para botones/select
const opcionesPrioridad = computed(() =>
  ['BAJA', 'MEDIA', 'ALTA', 'URGENTE'].map((value) => ({
    value,
    label: LABELS_PRIORIDAD[value] || value,
    color: COLORES_PRIORIDAD[value] || '#cbd5e1',
  }))
)

// Opciones sector para dropdown (nombre y número)
const opcionesSector = computed(() =>
  sectores.value.map((s) => ({
    value: s.id,
    label: `${s.nombre} (${s.numero})`,
    nombre: s.nombre,
  }))
)

// Sector seleccionado (objeto completo para obtener nombre)
const sectorSeleccionado = computed(() => {
  const id = form.value.sector_origen
  return sectores.value.find((s) => s.id === id) || null
})

// Advertencia: canal PAPEL o WHATSAPP sin sector ni emisor
const advertenciaOrigen = computed(() => {
  const canal = form.value.canal_ingreso
  if (!canal || (canal !== 'PRESENCIAL' && canal !== 'TELEFONO')) return null
  if (form.value.sector_origen || (form.value.emisor_externo || '').trim()) return null
  return 'Para Papel o WhatsApp se recomienda indicar sector de origen o emisor externo.'
})

// Contador de tema
const temaLength = computed(() => (form.value.tema || '').length)

// Fecha por defecto hoy (objeto Date para Calendar)
function fechaHoy() {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d
}

function limpiarErrores() {
  errores.value = {}
  errorGeneral.value = null
}

function validar() {
  const e = {}
  if (!form.value.canal_ingreso) e.canal_ingreso = 'El canal de ingreso es obligatorio.'
  if (!form.value.fecha_ingreso) e.fecha_ingreso = 'La fecha de ingreso es obligatoria.'
  const tema = (form.value.tema || '').trim()
  if (!tema) e.tema = 'El tema es obligatorio.'
  else if (tema.length < 5) e.tema = 'El tema debe tener al menos 5 caracteres.'
  else if (tema.length > MAX_TEMA) e.tema = `Máximo ${MAX_TEMA} caracteres.`
  if (!form.value.prioridad) e.prioridad = 'La prioridad es obligatoria.'

  const remitente = computarRemitente()
  const areaOrigen = computarAreaOrigen()
  if (!remitente) e.emisor_externo = 'Indicá sector de origen o emisor externo.'

  errores.value = e
  return Object.keys(e).length === 0
}

function computarRemitente() {
  if (sectorSeleccionado.value) return sectorSeleccionado.value.nombre
  return (form.value.emisor_externo || '').trim() || null
}

function computarAreaOrigen() {
  if (sectorSeleccionado.value) return sectorSeleccionado.value.nombre
  return 'Externo'
}

async function cargarSectores() {
  cargandoSectores.value = true
  try {
    const res = await get('/api/sectores/')
    sectores.value = Array.isArray(res) ? res : res.results || res
  } catch (err) {
    sectores.value = []
  } finally {
    cargandoSectores.value = false
  }
}

function initFechas() {
  if (!form.value.fecha_ingreso) form.value.fecha_ingreso = fechaHoy()
}

function agregarArchivos(files) {
  if (!files?.length) return
  const maxBytes = MAX_FILE_MB * 1024 * 1024
  for (const file of files) {
    const ext = '.' + (file.name.split('.').pop() || '').toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      toast.add({
        severity: 'warn',
        summary: 'Formato no permitido',
        detail: `${file.name}: solo PDF, DOC, DOCX, JPG, PNG.`,
      })
      continue
    }
    if (file.size > maxBytes) {
      toast.add({
        severity: 'warn',
        summary: 'Archivo muy grande',
        detail: `${file.name}: máximo ${MAX_FILE_MB} MB.`,
      })
      continue
    }
    adjuntos.value.push({
      file,
      tipo_adjunto: tipoAdjuntoNuevo.value,
      nombre_archivo: file.name,
    })
  }
}

function quitarAdjunto(index) {
  adjuntos.value.splice(index, 1)
}

function onDrop(e) {
  dropZoneActive.value = false
  e.preventDefault()
  agregarArchivos(e.dataTransfer?.files)
}

function onDragOver(e) {
  e.preventDefault()
  dropZoneActive.value = true
}

function onDragLeave() {
  dropZoneActive.value = false
}

function onFileSelect(e) {
  agregarArchivos(e.target?.files)
  e.target.value = ''
}

async function guardar() {
  limpiarErrores()
  if (!validar()) {
    errorGeneral.value = 'Revisá los campos marcados.'
    return
  }

  enviando.value = true
  errorGeneral.value = null
  try {
    const remitente = computarRemitente()
    const areaOrigen = computarAreaOrigen()
    const payload = {
      canal_ingreso: form.value.canal_ingreso,
      emisor_sector: form.value.sector_origen || null,
      numero_nota_externo: (form.value.numero_nota_externo || '').trim() || null,
      fecha_ingreso: formatearFechaParaApi(form.value.fecha_ingreso),
      fecha_limite: form.value.fecha_limite
        ? formatearFechaParaApi(form.value.fecha_limite)
        : null,
      remitente: remitente || 'Sin especificar',
      emisor_externo: (form.value.emisor_externo || '').trim() || null,
      area_origen: areaOrigen || 'General',
      tema: (form.value.tema || '').trim(),
      descripcion: (form.value.descripcion || '').trim() || '',
      prioridad: form.value.prioridad,
      genera_resolucion: !!form.value.genera_resolucion,
    }

    const nota = await post('/api/notas/', payload)
    const notaId = nota.id

    for (const adj of adjuntos.value) {
      const fd = new FormData()
      fd.append('nota', notaId)
      fd.append('tipo_adjunto', adj.tipo_adjunto)
      fd.append('nombre_archivo', adj.nombre_archivo)
      fd.append('archivo', adj.file)
      await postFormData(`/api/notas/${notaId}/adjuntos/`, fd)
    }

    toast.add({
      severity: 'success',
      summary: 'Nota creada',
      detail: `Nota ${nota.numero_nota_interno || notaId} creada correctamente.`,
    })
    router.push(`/notas/${notaId}`)
  } catch (err) {
    const data = err.data || {}
    if (data && typeof data === 'object') {
      for (const [key, value] of Object.entries(data)) {
        if (Array.isArray(value)) errores.value[key] = value[0]
        else errores.value[key] = String(value)
      }
    }
    errorGeneral.value =
      data.detalle || data.error || err.message || 'Error al guardar la nota.'
  } finally {
    enviando.value = false
  }
}

function formatearFechaParaApi(date) {
  if (!date) return null
  const d = date instanceof Date ? date : new Date(date)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function cancelar() {
  router.push('/notas')
}

onMounted(() => {
  cargarSectores()
  initFechas()
})
</script>

<template>
  <div class="nueva-nota-view min-h-full" style="background-color: #eef2f7">
    <div class="p-4 md:p-6 max-w-4xl mx-auto">
      <header class="mb-6">
        <h1 class="text-2xl md:text-3xl font-bold text-[#1e3a5f]">Nueva Nota</h1>
        <p class="text-gray-600 mt-1">Completá los datos de la nota</p>
      </header>

      <form @submit.prevent="guardar" class="space-y-6">
        <!-- Error general -->
        <div
          v-if="errorGeneral"
          class="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm"
        >
          {{ errorGeneral }}
        </div>

        <!-- Advertencia origen -->
        <div
          v-if="advertenciaOrigen"
          class="rounded-lg bg-amber-50 border border-amber-200 p-4 text-amber-800 text-sm"
        >
          {{ advertenciaOrigen }}
        </div>

        <!-- SECCIÓN 1 — Identificación -->
        <Card class="!bg-white !border !border-gray-200 !shadow-sm">
          <template #title>
            <span class="text-lg font-semibold text-[#1e3a5f]"
              >Identificación de la nota</span
            >
          </template>
          <template #content>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1"
                  >Canal de ingreso <span class="text-red-500">*</span></label
                >
                <Dropdown
                  v-model="form.canal_ingreso"
                  :options="opcionesCanal"
                  option-label="label"
                  option-value="value"
                  placeholder="Seleccionar"
                  class="w-full"
                  :class="{ 'border-red-500': errores.canal_ingreso }"
                />
                <p v-if="errores.canal_ingreso" class="text-red-600 text-sm mt-1">
                  {{ errores.canal_ingreso }}
                </p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1"
                  >Sector de origen</label
                >
                <Dropdown
                  v-model="form.sector_origen"
                  :options="opcionesSector"
                  option-label="label"
                  option-value="value"
                  placeholder="Seleccionar sector"
                  class="w-full"
                  :loading="cargandoSectores"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1"
                  >Número de nota externo</label
                >
                <InputText
                  v-model="form.numero_nota_externo"
                  placeholder="Ej: 138-023-2026 (dejar vacío si no tiene número)"
                  class="w-full"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1"
                  >Fecha de ingreso <span class="text-red-500">*</span></label
                >
                <Calendar
                  v-model="form.fecha_ingreso"
                  date-format="dd/mm/yy"
                  show-icon
                  class="w-full"
                  :class="{ 'border-red-500': errores.fecha_ingreso }"
                />
                <p v-if="errores.fecha_ingreso" class="text-red-600 text-sm mt-1">
                  {{ errores.fecha_ingreso }}
                </p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1"
                  >Fecha límite</label
                >
                <Calendar
                  v-model="form.fecha_limite"
                  date-format="dd/mm/yy"
                  show-icon
                  class="w-full"
                />
              </div>
            </div>
          </template>
        </Card>

        <!-- SECCIÓN 2 — Contenido -->
        <Card class="!bg-white !border !border-gray-200 !shadow-sm">
          <template #title>
            <span class="text-lg font-semibold text-[#1e3a5f]"
              >Contenido de la nota</span
            >
          </template>
          <template #content>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1"
                  >Tema <span class="text-red-500">*</span></label
                >
                <InputText
                  v-model="form.tema"
                  class="w-full"
                  :maxlength="MAX_TEMA"
                  :class="{ 'border-red-500': errores.tema }"
                />
                <div class="flex justify-between mt-1">
                  <p v-if="errores.tema" class="text-red-600 text-sm">
                    {{ errores.tema }}
                  </p>
                  <span class="text-gray-500 text-sm ml-auto"
                    >{{ temaLength }} / {{ MAX_TEMA }}</span
                  >
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1"
                  >Descripción</label
                >
                <Textarea
                  v-model="form.descripcion"
                  rows="4"
                  class="w-full"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1"
                  >Prioridad <span class="text-red-500">*</span></label
                >
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="opt in opcionesPrioridad"
                    :key="opt.value"
                    type="button"
                    :class="[
                      'px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors',
                      form.prioridad === opt.value
                        ? 'text-white border-transparent'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50',
                    ]"
                    :style="
                      form.prioridad === opt.value
                        ? { backgroundColor: opt.color, color: opt.value === 'BAJA' || opt.value === 'MEDIA' ? '#1e293b' : 'white' }
                        : {}
                    "
                    @click="form.prioridad = opt.value"
                  >
                    {{ opt.label }}
                  </button>
                </div>
                <p v-if="errores.prioridad" class="text-red-600 text-sm mt-1">
                  {{ errores.prioridad }}
                </p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1"
                  >Emisor externo</label
                >
                <InputText
                  v-model="form.emisor_externo"
                  placeholder="Nombre del remitente si no pertenece a un sector registrado"
                  class="w-full"
                  :class="{ 'border-red-500': errores.emisor_externo }"
                />
                <p v-if="errores.emisor_externo" class="text-red-600 text-sm mt-1">
                  {{ errores.emisor_externo }}
                </p>
              </div>
            </div>
          </template>
        </Card>

        <!-- SECCIÓN 3 — Asignación -->
        <Card class="!bg-white !border !border-gray-200 !shadow-sm">
          <template #title>
            <span class="text-lg font-semibold text-[#1e3a5f]">Asignación</span>
          </template>
          <template #content>
            <div class="flex items-center gap-2">
              <Checkbox
                v-model="form.genera_resolucion"
                input-id="genera_resolucion"
                :binary="true"
              />
              <label for="genera_resolucion" class="text-sm text-gray-700">
                Esta nota requiere confección de resolución formal
              </label>
            </div>
          </template>
        </Card>

        <!-- SECCIÓN 4 — Adjuntos -->
        <Card class="!bg-white !border !border-gray-200 !shadow-sm">
          <template #title>
            <span class="text-lg font-semibold text-[#1e3a5f]">Adjuntos</span>
          </template>
          <template #content>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1"
                  >Tipo de adjunto</label
                >
                <Dropdown
                  v-model="tipoAdjuntoNuevo"
                  :options="opcionesTipoAdjunto"
                  option-label="label"
                  option-value="value"
                  class="w-full max-w-xs"
                />
              </div>
              <div
                class="border-2 border-dashed rounded-xl p-8 text-center transition-colors"
                :class="
                  dropZoneActive
                    ? 'border-[#2d6a9f] bg-sky-50'
                    : 'border-gray-200 bg-gray-50'
                "
                @drop="onDrop"
                @dragover="onDragOver"
                @dragleave="onDragLeave"
              >
                <input
                  ref="fileInputRef"
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  class="hidden"
                  @change="onFileSelect"
                />
                <p class="text-gray-600 mb-2">
                  Arrastrá archivos aquí o
                  <button
                    type="button"
                    class="text-[#1e3a5f] font-medium underline"
                    @click="fileInputRef?.click()"
                  >
                    elegir archivos
                  </button>
                </p>
                <p class="text-sm text-gray-500">
                  PDF, DOC, DOCX, JPG, PNG. Máximo {{ MAX_FILE_MB }} MB por archivo.
                </p>
              </div>
              <ul v-if="adjuntos.length" class="space-y-2">
                <li
                  v-for="(adj, index) in adjuntos"
                  :key="index"
                  class="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg"
                >
                  <span class="text-sm text-gray-700 truncate flex-1 mr-2">{{
                    adj.nombre_archivo
                  }}</span>
                  <button
                    type="button"
                    class="text-red-600 hover:text-red-800 p-1"
                    aria-label="Eliminar"
                    @click="quitarAdjunto(index)"
                  >
                    <i class="pi pi-trash" />
                  </button>
                </li>
              </ul>
            </div>
          </template>
        </Card>

        <!-- Botones finales -->
        <div class="flex flex-wrap gap-3 justify-end">
          <button
            type="button"
            class="px-4 py-2 rounded-lg border border-gray-300 text-gray-600 bg-white hover:bg-gray-50 transition-colors text-sm font-medium"
            @click="cancelar"
          >
            Cancelar
          </button>
          <Button
            type="submit"
            label="Guardar"
            icon="pi pi-check"
            :loading="enviando"
            style="
              background-color: #1e3a5f !important;
              border-color: #1e3a5f !important;
              color: white !important;
            "
          />
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.nueva-nota-view {
  min-height: 100%;
}

/* Dropdowns con fondo blanco (consistente con NotasView) */
.nueva-nota-view :deep(.p-select),
.nueva-nota-view :deep(.p-select-overlay) {
  background-color: white !important;
  color: #1e293b !important;
  border: 1px solid #e2e8f0 !important;
}
.nueva-nota-view :deep(.p-select-option) {
  color: #1e293b !important;
}
.nueva-nota-view :deep(.p-select-option:hover) {
  background-color: #f1f5f9 !important;
}

.nueva-nota-view :deep(.p-button-label) {
  color: white !important;
}

/* Calendar (DatePicker) fondo blanco */
.nueva-nota-view :deep(.p-datepicker) {
  background-color: white !important;
  color: #1e293b !important;
  border: 1px solid #e2e8f0 !important;
}
</style>
