<script setup>
/**
 * NotasAsignadasView — Vista para OPERADOR con sus notas pendientes.
 * Ruta: /mis-notas
 * Tabs: Todas | Para iniciar (ASIGNADA) | En proceso | En espera
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useNotas } from '@/composables/useNotas'
import { ordenarPorPrioridadYFecha } from '@/utils/notas'
import TablaNotasSimple from '@/components/TablaNotasSimple.vue'
import BtnVolver from '@/components/BtnVolver.vue'

const route = useRoute()

const { notas, cargando, error, cargarPendientes } = useNotas()
cargando.value = true

const tabActivo = ref('todas')
const textoBusqueda = ref('')

const notasFiltradas = computed(() => {
  let lista = notas.value

  if (tabActivo.value !== 'todas') {
    lista = lista.filter((n) => n.estado === tabActivo.value)
  }

  const texto = (textoBusqueda.value || '').trim().toLowerCase()
  if (texto) {
    lista = lista.filter(
      (n) =>
        (n.numero_nota || '').toLowerCase().includes(texto) ||
        (n.numero_nota_interno || '').toLowerCase().includes(texto) ||
        (n.tema || '').toLowerCase().includes(texto),
    )
  }

  return lista
})

const notasOrdenadas = computed(() => ordenarPorPrioridadYFecha(notasFiltradas.value))

const totalNotas = computed(() => notasFiltradas.value.length)

onMounted(() => {
  const estadoQuery = route.query.estado
  if (estadoQuery && ['ASIGNADA', 'EN_PROCESO', 'EN_ESPERA'].includes(estadoQuery)) {
    tabActivo.value = estadoQuery
  }
  cargarPendientes()
})
</script>

<template>
  <div class="notas-asignadas min-h-full" style="background-color: #eef2f7">
    <div class="p-4 md:p-6">
      <header class="mb-6">
        <div v-if="route.query.estado" class="mb-3">
          <BtnVolver label="Inicio" destino="/" />
        </div>
        <h1 class="text-2xl md:text-3xl font-bold text-[#1e3a5f]">
          Notas Asignadas ({{ totalNotas }})
        </h1>
      </header>

      <div
        v-if="error"
        class="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm flex items-center justify-between gap-2"
      >
        <span>{{ error }}</span>
        <Button label="Reintentar" icon="pi pi-refresh" size="small" @click="cargarPendientes" />
      </div>

      <div class="mb-4">
        <div class="relative max-w-md">
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            v-model="textoBusqueda"
            type="text"
            placeholder="Buscar por número o tema"
            class="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg bg-white text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#2d6a9f] focus:border-transparent"
          />
        </div>
      </div>

      <div class="flex flex-wrap gap-2 mb-6">
        <button
          type="button"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="
            tabActivo === 'todas'
              ? 'bg-[#1e3a5f] text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          "
          @click="tabActivo = 'todas'"
        >
          Todas
        </button>
        <button
          type="button"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="
            tabActivo === 'ASIGNADA'
              ? 'bg-[#1e3a5f] text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          "
          @click="tabActivo = 'ASIGNADA'"
        >
          Para iniciar
        </button>
        <button
          type="button"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="
            tabActivo === 'EN_PROCESO'
              ? 'bg-[#1e3a5f] text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          "
          @click="tabActivo = 'EN_PROCESO'"
        >
          En proceso
        </button>
        <button
          type="button"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="
            tabActivo === 'EN_ESPERA'
              ? 'bg-[#1e3a5f] text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          "
          @click="tabActivo = 'EN_ESPERA'"
        >
          En espera
        </button>
      </div>

      <div v-if="cargando" class="flex justify-center py-12">
        <ProgressBar mode="indeterminate" style="height: 4px; width: 100%; max-width: 400px" />
      </div>

      <div v-else>
        <template v-if="notasFiltradas.length === 0">
          <div class="py-12 text-center text-gray-500 bg-white rounded-lg shadow-sm">
            <i class="pi pi-inbox text-4xl mb-2 block opacity-60" />
            <p>No hay notas en esta categoría.</p>
          </div>
        </template>
        <TablaNotasSimple
          v-else
          :notas="notasOrdenadas"
          :cargando="cargando"
          desde="mis-notas"
          :clickeable="false"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.notas-asignadas {
  min-height: 100%;
}
</style>
