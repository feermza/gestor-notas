<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { get, post, postFormData } from '@/api/cliente'
import { COLORES_PRIORIDAD, LABELS_PRIORIDAD } from '@/utils/notas'

const router = useRouter()
const toast = useToast()

// Datos de soporte
const sectores = ref([])
const usuarios = ref([])
const cargandoSectores = ref(true)
const cargandoUsuarios = ref(true)

// Formulario
const enviando = ref(false)
const errorGeneral = ref(null)

const form = ref({
  sector_origen_id: null,
  numero_nota_externo: '',
  tema: '',
  tarea_asignada: '',
  responsable_id: null,
  prioridad: 'MEDIA', // API usa MEDIA, se muestra como "Normal"
})

// Alias para usar en el template con el nombre solicitado
const formulario = form

const errores = ref({})

// Adjuntos: lista de { file, tipo_adjunto, nombre_archivo }
const adjuntos = ref([])
const fileInputRef = ref(null)

const MAX_TEMA = 100
const MAX_TAREA = 200
const MAX_FILE_MB = 10
const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']

// Fecha de ingreso (solo lectura, se calcula al montar)
const fechaIngreso = ref(new Date())
const anioActual = fechaIngreso.value.getFullYear()

// Sectores formateados para dropdown (ordenado por número)
const sectoresFormateados = computed(() =>
  [...sectores.value]
    .slice()
    .sort((a, b) => {
      const aNum = a.numero ?? 0
      const bNum = b.numero ?? 0
      return aNum - bNum
    })
    .map((s) => ({
      ...s,
      nombre_completo: `${s.numero} — ${s.nombre}`,
    }))
)

const sectorSeleccionado = computed(() => {
  const id = form.value.sector_origen_id
  return sectores.value.find((s) => s.id === id) || null
})

// Usuarios formateados para dropdown de responsable (excluye CONSULTOR)
const usuariosFormateados = computed(() =>
  usuarios.value
    .filter((u) => u.rol !== 'CONSULTOR')
    .map((u) => ({
      ...u,
      nombre_completo:
        u.nombre_completo ||
        `${u.apellido || ''}, ${u.nombres || ''} (${u.rol || ''})`.trim(),
    }))
)

// Prioridad: opciones con color para botones
const opcionesPrioridad = computed(() =>
  ['BAJA', 'MEDIA', 'ALTA', 'URGENTE'].map((value) => ({
    value,
    label: LABELS_PRIORIDAD[value] || value,
    color: COLORES_PRIORIDAD[value] || '#cbd5e1',
  }))
)

// Contadores
const temaLength = computed(() => (form.value.tema || '').length)
const tareaLength = computed(() => (form.value.tarea_asignada || '').length)

// Preview de numeración visual
const numeroNotaPreview = computed(() => {
  const numero = (form.value.numero_nota_externo || '').trim()
  const sector = sectorSeleccionado.value
  if (numero && sector && sector.numero) {
    return `El número de nota quedará: ${sector.numero}-${numero}-${anioActual}`
  }
  return `Se generará un número interno automáticamente (INT-XXXX-${anioActual})`
})

// Fechas
const fechaIngresoTexto = computed(() =>
  fechaIngreso.value.toLocaleString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
)

const fechaIngresoIso = computed(() => fechaIngreso.value.toISOString())

function limpiarErrores() {
  errores.value = {}
  errorGeneral.value = null
}

function validar() {
  const e = {}

  if (!form.value.sector_origen_id) {
    e.sector_origen = 'Debe seleccionar un sector de origen'
  }

  const tema = (form.value.tema || '').trim()
  if (!tema) e.tema = 'El tema es obligatorio.'
  else if (tema.length < 5) e.tema = 'El tema debe tener al menos 5 caracteres.'
  else if (tema.length > MAX_TEMA) e.tema = `Máximo ${MAX_TEMA} caracteres.`

  const tarea = (form.value.tarea_asignada || '').trim()
  if (!tarea) e.tarea_asignada = 'La tarea asignada es obligatoria.'
  else if (tarea.length < 10)
    e.tarea_asignada = 'La tarea asignada debe tener al menos 10 caracteres.'
  else if (tarea.length > MAX_TAREA)
    e.tarea_asignada = `Máximo ${MAX_TAREA} caracteres.`

  if (!form.value.responsable_id) {
    e.responsable_id = 'Debe seleccionar un responsable.'
  }

  errores.value = e
  return Object.keys(e).length === 0
}

async function cargarSectores() {
  cargandoSectores.value = true
  try {
    const res = await get('/api/sectores/')
    sectores.value = Array.isArray(res) ? res : res.results || res
  } catch (_err) {
    sectores.value = []
  } finally {
    cargandoSectores.value = false
  }
}

async function cargarUsuarios() {
  cargandoUsuarios.value = true
  try {
    const res = await get('/api/usuarios/?activos=true')
    usuarios.value = Array.isArray(res) ? res : res.results || res
  } catch (_err) {
    usuarios.value = []
  } finally {
    cargandoUsuarios.value = false
  }
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
      tipo_adjunto: 'DOCUMENTO_ORIGINAL',
      nombre_archivo: file.name,
    })
  }
}

function onFileSelect(e) {
  agregarArchivos(e.target?.files)
  e.target.value = ''
}

function quitarAdjunto(index) {
  adjuntos.value.splice(index, 1)
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
    const tema = (form.value.tema || '').trim()
    const tarea = (form.value.tarea_asignada || '').trim()
    const numeroExterno = (form.value.numero_nota_externo || '').trim() || null

    const payload = {
      sector_origen_id: form.value.sector_origen_id,
      numero_nota_externo: numeroExterno,
      fecha_ingreso: fechaIngresoIso.value,
      tema,
      tarea_asignada: tarea,
      responsable_id: form.value.responsable_id,
      prioridad: form.value.prioridad || 'MEDIA',
      estado: 'INGRESADA',
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
      detail: 'La nota se guardó correctamente.',
    })
    router.push('/notas')
  } catch (err) {
    const data = err.data || {}
    if (data && typeof data === 'object') {
      for (const [key, value] of Object.entries(data)) {
        const mensaje = Array.isArray(value) ? value[0] : String(value)
        if (key === 'sector_origen_id') errores.value.sector_origen = mensaje
        else if (key === 'responsable_id') errores.value.responsable_id = mensaje
        else if (key === 'tarea_asignada') errores.value.tarea_asignada = mensaje
        else if (key === 'numero_nota_externo')
          errores.value.numero_nota_externo = mensaje
        else errores.value[key] = mensaje
      }
    }
    errorGeneral.value =
      data.detalle || data.error || err.message || 'Error al guardar la nota.'
  } finally {
    enviando.value = false
  }
}

function cancelar() {
  router.push('/notas')
}

onMounted(() => {
  cargarSectores()
  cargarUsuarios()
})
</script>

<template>
  <div class="nueva-nota min-h-full" style="background-color: #eef2f7">
    <div class="p-4 md:p-6 max-w-4xl mx-auto">
      <header class="mb-6">
        <h1 class="text-2xl md:text-3xl font-bold text-[#1e3a5f]">Nueva nota</h1>
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

        <!-- SECCIÓN 1 — Identificación -->
        <Card>
          <template #title>Identificación</template>
          <template #content>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Sector de origen -->
              <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Sector de origen <span class="text-red-500">*</span>
                </label>
                <Dropdown
                  v-model="formulario.sector_origen_id"
                  :options="sectoresFormateados"
                  option-label="nombre_completo"
                  option-value="id"
                  placeholder="Seleccionar sector de origen"
                  class="w-full"
                  :loading="cargandoSectores"
                  :class="{ 'border-red-500': errores.sector_origen }"
                />
                <p v-if="errores.sector_origen" class="text-red-600 text-sm mt-1">
                  {{ errores.sector_origen }}
                </p>
              </div>

              <!-- Número de nota externo -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Número de nota externo
                </label>
                <InputText
                  v-model="form.numero_nota_externo"
                  placeholder="Ej: 023 (solo el número, sin año ni sector)"
                  class="w-full"
                />
                <p class="text-xs text-gray-500 mt-1">
                  Si la nota no tiene número, se generará uno automáticamente
                </p>
                <p class="text-xs text-gray-400 mt-1">
                  {{ numeroNotaPreview }}
                </p>
              </div>

              <!-- Fecha de ingreso (solo lectura) -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Fecha de ingreso
                </label>
                <div
                  class="px-3 py-2 rounded border border-gray-200 bg-gray-50 text-sm text-gray-700 flex items-center justify-between"
                >
                  <span>{{ fechaIngresoTexto }}</span>
                  <span class="text-xs text-gray-400">Solo lectura</span>
                </div>
              </div>
            </div>
          </template>
        </Card>

        <!-- SECCIÓN 2 — Contenido -->
        <Card>
          <template #title>Contenido</template>
          <template #content>
            <div class="space-y-4">
              <!-- Tema -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Tema <span class="text-red-500">*</span>
                </label>
                <InputText
                  v-model="formulario.tema"
                  class="w-full"
                  :maxlength="MAX_TEMA"
                  placeholder="Resumen breve del asunto de la nota"
                  :class="{ 'border-red-500': errores.tema }"
                />
                <div class="flex justify-between mt-1">
                  <p v-if="errores.tema" class="text-red-600 text-sm">
                    {{ errores.tema }}
                  </p>
                  <span class="text-gray-500 text-sm ml-auto">
                    {{ temaLength }} / {{ MAX_TEMA }}
                  </span>
                </div>
              </div>

              <!-- Tarea asignada -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Tarea a ejecutar <span class="text-red-500">*</span>
                </label>
                <InputText
                  v-model="formulario.tarea_asignada"
                  class="w-full"
                  :maxlength="MAX_TAREA"
                  placeholder="Describí la acción concreta que debe realizar el responsable"
                  :class="{ 'border-red-500': errores.tarea_asignada }"
                />
                <p class="text-xs text-gray-500 mt-1">
                  Ej: Verificar antigüedad y emitir resolución de licencia
                </p>
                <div class="flex justify-between mt-1">
                  <p v-if="errores.tarea_asignada" class="text-red-600 text-sm">
                    {{ errores.tarea_asignada }}
                  </p>
                  <span class="text-gray-500 text-sm ml-auto">
                    {{ tareaLength }} / {{ MAX_TAREA }}
                  </span>
                </div>
              </div>

              <!-- Responsable -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Responsable <span class="text-red-500">*</span>
                </label>
                <Dropdown
                  v-model="formulario.responsable_id"
                  :options="usuariosFormateados"
                  option-label="nombre_completo"
                  option-value="id"
                  placeholder="Seleccionar responsable"
                  class="w-full"
                  :loading="cargandoUsuarios"
                  :class="{ 'border-red-500': errores.responsable_id }"
                />
                <p v-if="errores.responsable_id" class="text-red-600 text-sm mt-1">
                  {{ errores.responsable_id }}
                </p>
              </div>
            </div>
          </template>
        </Card>

        <!-- SECCIÓN 3 — Adjuntos y opciones -->
        <Card>
          <template #title>Adjuntos y opciones</template>
          <template #content>
            <div class="space-y-4">
              <!-- Adjuntos -->
              <div>
                <input
                  ref="fileInputRef"
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  class="hidden"
                  @change="onFileSelect"
                />
                <Button
                  type="button"
                  label="Adjuntar archivo"
                  icon="pi pi-paperclip"
                  class="px-4 py-2"
                  @click="fileInputRef?.click()"
                />
                <p class="text-sm text-gray-500 mt-2">
                  PDF, DOC, DOCX, JPG, PNG (máx {{ MAX_FILE_MB }} MB por archivo)
                </p>
              </div>

              <ul v-if="adjuntos.length" class="space-y-2">
                <li
                  v-for="(adj, index) in adjuntos"
                  :key="index"
                  class="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg"
                >
                  <span class="text-sm text-gray-700 truncate flex-1 mr-2">
                    {{ adj.nombre_archivo }}
                  </span>
                  <button
                    type="button"
                    class="text-red-600 hover:text-red-800 p-1"
                    aria-label="Eliminar"
                    @click="quitarAdjunto(index)"
                  >
                    <i class="pi pi-times" />
                  </button>
                </li>
              </ul>

              <!-- Prioridad -->
              <div class="border-t border-gray-200 pt-4 mt-2">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Prioridad (opcional)
                </label>
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
                        ? {
                            backgroundColor: opt.color,
                            color:
                              opt.value === 'BAJA' || opt.value === 'MEDIA'
                                ? '#1e293b'
                                : 'white',
                          }
                        : {}
                    "
                    @click="form.prioridad = opt.value"
                  >
                    {{ opt.label }}
                  </button>
                </div>
              </div>
            </div>
          </template>
        </Card>

        <!-- Botones finales -->
        <div class="flex flex-col items-end gap-2 pt-2">
          <p class="text-xs text-gray-400">
            Debug: sector={{ formulario.sector_origen_id }}, responsable={{ formulario.responsable_id }}
          </p>
          <div class="flex flex-wrap gap-3 justify-end w-full">
          <button
            type="button"
            class="px-4 py-2 rounded-lg border border-gray-300 text-gray-600 bg-white hover:bg-gray-50 transition-colors text-sm font-medium"
            @click="cancelar"
          >
            Cancelar
          </button>
          <Button
            type="submit"
            label="Guardar nota"
            icon="pi pi-save"
            :loading="enviando"
            :disabled="
              !formulario.sector_origen_id ||
              !formulario.tema ||
              formulario.tema.length < 5 ||
              !formulario.tarea_asignada ||
              formulario.tarea_asignada.length < 10 ||
              !formulario.responsable_id ||
              enviando
            "
            class="text-sm font-medium"
            style="
              background-color: #1e3a5f !important;
              border-color: #1e3a5f !important;
              color: white !important;
            "
          />
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.nueva-nota {
  min-height: 100%;
}

.nueva-nota :deep(.p-select),
.nueva-nota :deep(.p-inputtext),
.nueva-nota :deep(.p-textarea) {
  background-color: white !important;
  color: #1e293b !important;
  border: 1px solid #e2e8f0 !important;
}

.nueva-nota :deep(.p-select-overlay) {
  background-color: white !important;
}

.nueva-nota :deep(.p-select-option) {
  color: #1e293b !important;
  background-color: white !important;
}

.nueva-nota :deep(.p-select-option:hover) {
  background-color: #f1f5f9 !important;
}

.nueva-nota :deep(.p-card) {
  background-color: white !important;
  color: #1e293b !important;
}

.nueva-nota :deep(.p-card-title) {
  color: #1e3a5f !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
}
</style>
