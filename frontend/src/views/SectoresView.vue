<script setup>
/**
 * SectoresView — Gestión de sectores (solo ADMINISTRADOR).
 * Listado, búsqueda, modal nuevo/editar, activar/desactivar.
 */
import { ref, computed, onMounted } from 'vue'
import { get, post, patch } from '@/api/cliente'

// Estado
const sectores = ref([])
const cargando = ref(true)
const error = ref(null)
const textoBusqueda = ref('')

// Toasts personalizados
const mensajeExito = ref('')
const mostrarExito = ref(false)
const mensajeError = ref('')
const mostrarError = ref(false)

function mostrarToastExito(mensaje) {
  mensajeExito.value = mensaje
  mostrarExito.value = true
  setTimeout(() => {
    mostrarExito.value = false
  }, 3000)
}

function mostrarToastError(mensaje) {
  mensajeError.value = mensaje
  mostrarError.value = true
  setTimeout(() => {
    mostrarError.value = false
  }, 4000)
}

// Modal nuevo/editar
const dialogVisible = ref(false)
const enviando = ref(false)
const sectorEditId = ref(null)
const form = ref({
  numero: '',
  nombre: '',
  email: '',
  descripcion: '',
  activo: true,
})

const esNuevo = computed(() => sectorEditId.value == null)
const tituloModal = computed(() => (esNuevo.value ? 'Nuevo sector' : 'Editar sector'))

// Sectores filtrados por búsqueda (nombre o número)
const sectoresFiltrados = computed(() => {
  const t = (textoBusqueda.value || '').trim().toLowerCase()
  if (!t) return sectores.value
  return sectores.value.filter(
    (s) =>
      (String(s.numero ?? '')).toLowerCase().includes(t) ||
      (s.nombre || '').toLowerCase().includes(t) ||
      (s.email || '').toLowerCase().includes(t),
  )
})

const totalSectores = computed(() => sectoresFiltrados.value.length)

async function cargarSectores() {
  cargando.value = true
  error.value = null
  try {
    const res = await get('/api/sectores/')
    sectores.value = Array.isArray(res) ? res : res.results || []
  } catch (e) {
    error.value = e?.data?.detalle || e?.data?.detail || e?.message || 'Error al cargar sectores.'
  } finally {
    cargando.value = false
  }
}

function abrirNuevo() {
  sectorEditId.value = null
  form.value = {
    numero: '',
    nombre: '',
    email: '',
    descripcion: '',
    activo: true,
  }
  dialogVisible.value = true
}

function abrirEditar(sector) {
  sectorEditId.value = sector.id
  form.value = {
    numero: String(sector.numero ?? ''),
    nombre: sector.nombre || '',
    email: sector.email || '',
    descripcion: sector.descripcion || '',
    activo: sector.activo ?? true,
  }
  dialogVisible.value = true
}

function validar() {
  const f = form.value
  if (!String(f.numero ?? '').trim()) return 'El número es obligatorio.'
  if (!(f.nombre || '').trim()) return 'El nombre es obligatorio.'
  const num = parseInt(String(f.numero).trim(), 10)
  if (isNaN(num) || num < 0) return 'El número debe ser un valor numérico válido.'
  return null
}

async function guardar() {
  const err = validar()
  if (err) {
    mostrarToastError(err)
    return
  }
  enviando.value = true
  try {
    const payload = {
      numero: parseInt(String(form.value.numero).trim(), 10),
      nombre: (form.value.nombre || '').trim(),
      email: (form.value.email || '').trim(),
      descripcion: (form.value.descripcion || '').trim(),
      activo: form.value.activo,
    }
    if (esNuevo.value) {
      await post('/api/sectores/', payload)
      mostrarToastExito('Sector creado correctamente.')
    } else {
      await patch(`/api/sectores/${sectorEditId.value}/`, payload)
      mostrarToastExito('Sector actualizado correctamente.')
    }
    dialogVisible.value = false
    await cargarSectores()
  } catch (e) {
    const d = e?.data
    let msg = d?.detalle || d?.detail || e?.message || 'Error al guardar el sector.'
    if (d && typeof d === 'object') {
      const first = d.numero?.[0] || d.nombre?.[0] || d.email?.[0]
      if (first) msg = first
    }
    mostrarToastError(msg)
  } finally {
    enviando.value = false
  }
}

async function toggleActivo(sector) {
  try {
    const nuevoActivo = !(sector.activo ?? true)
    await patch(`/api/sectores/${sector.id}/`, { activo: nuevoActivo })
    mostrarToastExito(nuevoActivo ? 'Sector activado.' : 'Sector desactivado.')
    await cargarSectores()
  } catch (e) {
    const msg = e?.data?.detalle || e?.data?.detail || e?.message || 'Error al cambiar el estado.'
    mostrarToastError(msg)
  }
}

onMounted(() => {
  cargarSectores()
})
</script>

<template>
  <div class="sectores-view min-h-full" style="background-color: #eef2f7">
    <!-- Toasts -->
    <Transition name="slide-down">
      <div
        v-if="mostrarExito"
        class="fixed top-4 right-4 z-[9999] flex items-center gap-3 bg-[#059669] text-white px-5 py-3 rounded-lg shadow-lg"
      >
        <i class="pi pi-check-circle text-lg" />
        <span class="font-medium">{{ mensajeExito }}</span>
      </div>
    </Transition>
    <Transition name="slide-down">
      <div
        v-if="mostrarError"
        class="fixed top-4 right-4 z-[9999] flex items-center gap-3 bg-[#dc2626] text-white px-5 py-3 rounded-lg shadow-lg"
      >
        <i class="pi pi-times-circle text-lg" />
        <span class="font-medium">{{ mensajeError }}</span>
      </div>
    </Transition>

    <div class="p-4 md:p-6">
      <header class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 class="text-2xl md:text-3xl font-bold text-[#1e3a5f]">
          Sectores ({{ totalSectores }})
        </h1>
        <Button
          label="Nuevo Sector"
          icon="pi pi-plus"
          class="font-medium"
          style="
            background-color: #1e3a5f !important;
            border-color: #1e3a5f !important;
            color: white !important;
          "
          @click="abrirNuevo"
        />
      </header>

      <div
        v-if="error"
        class="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm flex items-center justify-between gap-2"
      >
        <span>{{ error }}</span>
        <Button label="Reintentar" icon="pi pi-refresh" size="small" @click="cargarSectores" />
      </div>

      <div class="mb-4">
        <div class="relative max-w-md">
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 z-10" />
          <input
            v-model="textoBusqueda"
            type="text"
            placeholder="Buscar por nombre o número"
            class="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg bg-white text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#2d6a9f] focus:border-transparent"
          />
        </div>
      </div>

      <div v-if="cargando" class="mb-4">
        <ProgressBar mode="indeterminate" style="height: 4px" />
      </div>

      <div v-if="!cargando" class="card rounded-xl overflow-hidden shadow-md">
        <DataTable
          :value="sectoresFiltrados"
          data-key="id"
          striped-rows
          responsive-layout="stack"
          breakpoint="960px"
          class="p-datatable-sm"
          current-page-report-template="Mostrando {first} a {last} de {totalRecords} sectores"
          paginator
          :rows="10"
          :rows-per-page-options="[10, 25, 50]"
        >
          <Column field="numero" header="Número" sortable />
          <Column field="nombre" header="Nombre" sortable />
          <Column field="email" header="Email">
            <template #body="{ data }">
              {{ data.email || '—' }}
            </template>
          </Column>
          <Column header="Estado">
            <template #body="{ data }">
              <span
                :class="
                  (data.activo ?? true)
                    ? 'bg-[#059669] text-white'
                    : 'bg-[#dc2626] text-white'
                "
                class="px-2 py-0.5 rounded text-xs font-medium"
              >
                {{ (data.activo ?? true) ? 'Activo' : 'Inactivo' }}
              </span>
            </template>
          </Column>
          <Column header="Acciones" class="acciones-col">
            <template #body="{ data }">
              <Button
                icon="pi pi-pencil"
                text
                rounded
                severity="secondary"
                size="small"
                v-tooltip.top="'Editar'"
                @click="abrirEditar(data)"
              />
              <Button
                icon="pi pi-power-off"
                text
                rounded
                size="small"
                :class="(data.activo ?? true) ? 'text-green-600' : 'text-red-600'"
                v-tooltip.top="
                  (data.activo ?? true) ? 'Desactivar sector' : 'Activar sector'
                "
                @click="toggleActivo(data)"
              />
            </template>
          </Column>
          <template #empty>
            <div class="py-8 text-center text-gray-500">
              <i class="pi pi-building text-4xl mb-2 block opacity-60" />
              <p>{{ error ? 'Error al cargar.' : 'No hay sectores.' }}</p>
            </div>
          </template>
        </DataTable>
      </div>
    </div>

    <!-- Modal Nuevo / Editar -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="tituloModal"
      :modal="true"
      :closable="true"
      :style="{ width: '480px' }"
      class="sectores-view"
      @hide="dialogVisible = false"
    >
      <form @submit.prevent="guardar" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >Número <span class="text-red-500">*</span></label
          >
          <InputText
            v-model="form.numero"
            type="text"
            placeholder="Ej: 138"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >Nombre <span class="text-red-500">*</span></label
          >
          <InputText v-model="form.nombre" class="w-full" placeholder="Ej: Mesa de Entradas" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <InputText
            v-model="form.email"
            type="email"
            class="w-full"
            placeholder="sector@ejemplo.com"
          />
          <p class="text-xs text-gray-400 mt-1">
            Email institucional del sector. Si no tiene, dejarlo vacío.
          </p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
          <Textarea
            v-model="form.descripcion"
            class="w-full"
            rows="3"
            placeholder="Descripción opcional"
          />
        </div>
      </form>
      <template #footer>
        <div class="flex justify-end gap-3 px-2 py-2">
          <Button
            label="Cancelar"
            @click="dialogVisible = false"
            style="
              background-color: transparent !important;
              border: 2px solid white !important;
              color: #1e3a5f !important;
              font-weight: 500;
            "
          />
          <Button
            label="Guardar"
            icon="pi pi-check"
            :loading="enviando"
            @click="guardar"
            style="
              background-color: #1e3a5f !important;
              border-color: #1e3a5f !important;
              color: white !important;
            "
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.sectores-view {
  min-height: 100%;
}
</style>
