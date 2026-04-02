<script setup>
/**
 * UsuariosView — Gestión de usuarios (solo ADMINISTRADOR).
 * Listado, búsqueda, modal nuevo/editar, activar/desactivar.
 */
import { ref, computed, onMounted } from 'vue'
import { get, post, patch } from '@/api/cliente'
import { toArray } from '@/utils/notas'

// Estado
const usuarios = ref([])
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
const usuarioEditId = ref(null)
const form = ref({
  legajo: '',
  apellido: '',
  nombres: '',
  dni: '',
  email: '',
  rol: 'OPERADOR',
  password: '',
  activo: true,
})

const esNuevo = computed(() => usuarioEditId.value == null)
const tituloModal = computed(() => (esNuevo.value ? 'Nuevo usuario' : 'Editar usuario'))
const usuarioEditando = computed(
  () => usuarios.value.find((u) => u.id === usuarioEditId.value) || null,
)

const OPCIONES_ROL = [
  { value: 'ADMINISTRADOR', label: 'Administrador' },
  { value: 'SUPERVISOR', label: 'Supervisor' },
  { value: 'OPERADOR', label: 'Operador' },
  { value: 'CONSULTOR', label: 'Consultor' },
]

const colorRol = (rol) => {
  const map = {
    ADMINISTRADOR: 'bg-[#7c3aed]',
    SUPERVISOR: 'bg-[#0891b2]',
    OPERADOR: 'bg-[#1d4ed8]',
    CONSULTOR: 'bg-[#475569]',
  }
  return map[rol] || 'bg-gray-500'
}

// Usuarios filtrados por búsqueda (legajo, nombre, email)
const usuariosFiltrados = computed(() => {
  const t = (textoBusqueda.value || '').trim().toLowerCase()
  if (!t) return usuarios.value
  return usuarios.value.filter(
    (u) =>
      (u.legajo || '').toLowerCase().includes(t) ||
      (u.nombre_completo || '').toLowerCase().includes(t) ||
      (u.apellido || '').toLowerCase().includes(t) ||
      (u.nombres || '').toLowerCase().includes(t) ||
      (u.email || '').toLowerCase().includes(t),
  )
})

const totalUsuarios = computed(() => usuariosFiltrados.value.length)

async function cargarUsuarios() {
  cargando.value = true
  error.value = null
  try {
    const res = await get('/api/usuarios/')
    usuarios.value = toArray(res)
  } catch (e) {
    error.value = e?.data?.detalle || e?.data?.detail || e?.message || 'Error al cargar usuarios.'
  } finally {
    cargando.value = false
  }
}

function abrirNuevo() {
  usuarioEditId.value = null
  form.value = {
    legajo: '',
    apellido: '',
    nombres: '',
    dni: '',
    email: '',
    rol: 'OPERADOR',
    password: '',
    activo: true,
  }
  dialogVisible.value = true
}

function abrirEditar(usuario) {
  usuarioEditId.value = usuario.id
  form.value = {
    legajo: usuario.legajo || '',
    apellido: usuario.apellido || '',
    nombres: usuario.nombres || '',
    dni: usuario.dni || '',
    email: usuario.email || '',
    rol: usuario.rol || 'OPERADOR',
    password: '',
    activo: usuario.activo ?? usuario.is_active ?? true,
  }
  dialogVisible.value = true
}

function validar() {
  const f = form.value
  if (!String(f.legajo ?? '').trim()) return 'El legajo es obligatorio.'
  if (!(f.apellido || '').trim()) return 'El apellido es obligatorio.'
  if (!(f.nombres || '').trim()) return 'Los nombres son obligatorios.'
  if (!(f.dni || '').trim()) return 'El DNI es obligatorio.'
  if (!(f.email || '').trim()) return 'El email es obligatorio.'
  return null
}

async function guardar() {
  const err = validar()
  console.log('Error de validación:', err)
  if (err) {
    console.log('Llamando mostrarToastError con:', err)
    mostrarToastError(err)
    return
  }
  enviando.value = true
  try {
    const payload = {
      legajo: String(form.value.legajo ?? '').trim(),
      apellido: (form.value.apellido || '').trim(),
      nombres: (form.value.nombres || '').trim(),
      dni: (form.value.dni || '').trim(),
      email: (form.value.email || '').trim(),
      rol: form.value.rol,
      activo: form.value.activo,
    }
    if (!esNuevo.value && (form.value.password || '').trim()) {
      payload.password = form.value.password.trim()
    }
    if (esNuevo.value) {
      await post('/api/usuarios/', payload)
      mostrarToastExito('Usuario creado correctamente.')
    } else {
      await patch(`/api/usuarios/${usuarioEditId.value}/`, payload)
      mostrarToastExito('Usuario actualizado correctamente.')
    }
    dialogVisible.value = false
    await cargarUsuarios()
  } catch (e) {
    const d = e?.data
    let msg = d?.detalle || d?.detail || e?.message || 'Error al guardar el usuario.'
    if (d && typeof d === 'object') {
      const first = d.email?.[0] || d.legajo?.[0] || d.dni?.[0]
      if (first) msg = first
    }
    mostrarToastError(msg)
  } finally {
    enviando.value = false
  }
}

async function toggleActivo(usuario) {
  try {
    if (usuario.activo ?? usuario.is_active) {
      await post(`/api/usuarios/${usuario.id}/desactivar/`, {})
      mostrarToastExito('Usuario desactivado.')
    } else {
      await post(`/api/usuarios/${usuario.id}/activar/`, {})
      mostrarToastExito('Usuario activado.')
    }
    await cargarUsuarios()
  } catch (e) {
    const msg = e?.data?.detalle || e?.data?.detail || e?.message || 'Error al cambiar el estado.'
    mostrarToastError(msg)
  }
}

async function confirmarResetPassword() {
  const u = usuarioEditando.value
  if (!u) return
  const nombre =
    u.nombre_completo || `${u.apellido || ''}, ${u.nombres || ''}`.trim() || 'este usuario'
  const nuevaPass = `Rrhh${u.legajo}!`
  if (confirm(`¿Resetear contraseña de ${nombre}?\n\nNueva contraseña: ${nuevaPass}`)) {
    try {
      await post(`/api/usuarios/${u.id}/resetear_password/`, {})
      mostrarToastExito('Contraseña reseteada correctamente.')
    } catch (e) {
      const msg =
        e?.data?.detalle || e?.data?.detail || e?.message || 'Error al resetear contraseña.'
      mostrarToastError(msg)
    }
  }
}

onMounted(() => {
  cargarUsuarios()
})
</script>

<template>
  <div class="usuarios-view min-h-full" style="background-color: #eef2f7">
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
          Usuarios ({{ totalUsuarios }})
        </h1>
        <Button
          label="Nuevo Usuario"
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
        <Button label="Reintentar" icon="pi pi-refresh" size="small" @click="cargarUsuarios" />
      </div>

      <div class="mb-4">
        <div class="relative max-w-md">
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 z-10" />
          <input
            v-model="textoBusqueda"
            type="text"
            placeholder="Buscar por legajo, nombre o email"
            class="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg bg-white text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#2d6a9f] focus:border-transparent"
          />
        </div>
      </div>

      <div v-if="cargando" class="mb-4">
        <ProgressBar mode="indeterminate" style="height: 4px" />
      </div>

      <div v-if="!cargando" class="card rounded-xl overflow-hidden shadow-md">
        <DataTable
          :value="usuariosFiltrados"
          data-key="id"
          striped-rows
          responsive-layout="stack"
          breakpoint="960px"
          class="p-datatable-sm"
          current-page-report-template="Mostrando {first} a {last} de {totalRecords} usuarios"
          paginator
          :rows="10"
          :rows-per-page-options="[10, 25, 50]"
        >
          <Column field="legajo" header="Legajo" sortable />
          <Column header="Nombre completo">
            <template #body="{ data }">
              {{
                data.nombre_completo ||
                `${data.apellido || ''}, ${data.nombres || ''}`.trim() ||
                '—'
              }}
            </template>
          </Column>
          <Column field="dni" header="DNI">
            <template #body="{ data }">
              {{ data.dni || '—' }}
            </template>
          </Column>
          <Column field="email" header="Email" />
          <Column header="Rol">
            <template #body="{ data }">
              <span
                :class="[colorRol(data.rol), 'text-white px-2 py-0.5 rounded text-xs font-medium']"
              >
                {{ data.rol || '—' }}
              </span>
            </template>
          </Column>
          <Column header="Estado">
            <template #body="{ data }">
              <span
                :class="
                  (data.activo ?? data.is_active)
                    ? 'bg-[#059669] text-white'
                    : 'bg-[#dc2626] text-white'
                "
                class="px-2 py-0.5 rounded text-xs font-medium"
              >
                {{ (data.activo ?? data.is_active) ? 'Activo' : 'Inactivo' }}
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
                :icon="(data.activo ?? data.is_active) ? 'pi pi-power-off' : 'pi pi-power-off'"
                text
                rounded
                size="small"
                :class="(data.activo ?? data.is_active) ? 'text-green-600' : 'text-red-600'"
                v-tooltip.top="
                  (data.activo ?? data.is_active) ? 'Desactivar usuario' : 'Activar usuario'
                "
                @click="toggleActivo(data)"
              />
            </template>
          </Column>
          <template #empty>
            <div class="py-8 text-center text-gray-500">
              <i class="pi pi-users text-4xl mb-2 block opacity-60" />
              <p>{{ error ? 'Error al cargar.' : 'No hay usuarios.' }}</p>
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
      class="usuarios-view"
      @hide="dialogVisible = false"
    >
      <form @submit.prevent="guardar" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >Legajo <span class="text-red-500">*</span></label
          >
          <InputNumber
            v-model="form.legajo"
            input-id="legajo"
            placeholder="Número de legajo"
            class="w-full"
            :use-grouping="false"
          />
          <div
            v-if="esNuevo && String(form.legajo ?? '').trim().length > 0"
            class="text-sm text-[#0891b2] bg-blue-50 rounded-lg px-3 py-2 flex items-center gap-2 mt-2"
          >
            <i class="pi pi-info-circle" />
            <span
              >La contraseña inicial será
              <strong>Rrhh{{ String(form.legajo ?? '') }}!</strong></span
            >
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >Apellido <span class="text-red-500">*</span></label
          >
          <InputText v-model="form.apellido" class="w-full" placeholder="Apellido" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >Nombres <span class="text-red-500">*</span></label
          >
          <InputText v-model="form.nombres" class="w-full" placeholder="Nombres" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >DNI <span class="text-red-500">*</span></label
          >
          <InputText v-model="form.dni" class="w-full" placeholder="DNI" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >Email <span class="text-red-500">*</span></label
          >
          <InputText
            v-model="form.email"
            type="email"
            class="w-full"
            placeholder="email@ejemplo.com"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >Rol <span class="text-red-500">*</span></label
          >
          <Dropdown
            v-model="form.rol"
            :options="OPCIONES_ROL"
            option-label="label"
            option-value="value"
            placeholder="Seleccionar rol"
            class="w-full"
          />
        </div>
        <div v-if="!esNuevo">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Contraseña (dejar en blanco para no cambiar)
          </label>
          <Password
            v-model="form.password"
            class="w-full"
            placeholder="Contraseña"
            :feedback="false"
            toggle-mask
          />
          <button
            type="button"
            class="w-full mt-2 py-2 px-4 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm transition-colors flex items-center justify-center"
            @click="confirmarResetPassword"
          >
            <i class="pi pi-refresh mr-2" />
            Resetear contraseña
          </button>
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
.usuarios-view {
  min-height: 100%;
}
</style>
