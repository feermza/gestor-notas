<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { COLORES_ESTADO, haceCuanto } from '@/utils/notas'
import BadgeEstado from '@/components/BadgeEstado.vue'
import BadgePrioridad from '@/components/BadgePrioridad.vue'

defineProps({
  notas: { type: Array, required: true },
  cargando: { type: Boolean, default: false },
  desde: { type: String, default: 'notas' },
})

const router = useRouter()
const hoverId = ref(null)
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100">
    <div class="tabla-header">
      <span class="flex items-center text-left">Número</span>
      <span class="flex items-center text-left">Tema</span>
      <span class="flex items-center text-left">Estado</span>
      <span class="flex items-center text-left">Prioridad</span>
      <span class="flex items-center text-left">Responsable</span>
      <span class="flex items-center text-left">Fecha</span>
      <span class="flex items-center text-left"></span>
    </div>

    <div v-if="cargando" class="p-8 text-center text-gray-400">
      <i class="pi pi-spin pi-spinner text-2xl" />
    </div>

    <div v-else-if="notas.length === 0" class="p-8 text-center text-gray-400">
      <i class="pi pi-inbox text-3xl mb-2 block opacity-60" />
      <p class="text-sm">No hay notas para mostrar</p>
    </div>

    <ul v-else class="divide-y divide-gray-100">
      <li
        v-for="nota in notas"
        :key="nota.id"
        class="tabla-fila"
        @mouseenter="hoverId = nota.id"
        @mouseleave="hoverId = null"
        :style="{
          borderLeftColor: hoverId === nota.id ? COLORES_ESTADO[nota.estado] : 'transparent',
        }"
      >
        <span class="font-mono text-sm font-bold text-[#1e3a5f] truncate">
          {{ nota.numero_nota }}
        </span>
        <span class="text-sm text-gray-700 truncate" :title="nota.tema">
          {{ nota.tema }}
        </span>
        <BadgeEstado :estado="nota.estado" />
        <span class="justify-self-start">
          <BadgePrioridad :prioridad="nota.prioridad" />
        </span>
        <span class="text-sm text-gray-600 truncate">
          {{ nota.responsable?.nombre_completo || 'Sin asignar' }}
        </span>
        <span class="text-xs text-gray-600">
          {{ haceCuanto(nota.fecha_ingreso) }}
        </span>
        <span class="flex justify-end" @click.stop>
          <img
            src="/images/ver-detalles.png"
            alt="Ver detalle"
            v-tooltip.left="'Ver detalle'"
            @click.stop="router.push(`/notas/${nota.id}?desde=${desde}`)"
            class="w-4 h-4 cursor-pointer opacity-60 hover:opacity-100 transition-opacity duration-200"
          />
        </span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.tabla-header {
  display: grid;
  grid-template-columns: 140px 1fr 130px 110px 160px 80px 50px;
  gap: 16px;
  padding: 10px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  align-items: center;
}
.tabla-fila {
  display: grid;
  grid-template-columns: 140px 1fr 130px 110px 160px 80px 50px;
  gap: 16px;
  padding: 10px 16px;
  align-items: center;
  background: white;
  border-left: 3px solid transparent;
  transition: all 0.15s;
  cursor: default;
}
.tabla-fila:hover {
  background: #d2d7e4;
}
</style>
