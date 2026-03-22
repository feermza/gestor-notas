<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { COLORES_ESTADO } from '@/utils/notas'
import BtnDetalle from '@/components/BtnDetalle.vue'
import BadgeEstado from '@/components/BadgeEstado.vue'

defineProps({
  notas: { type: Array, required: true },
  cargando: { type: Boolean, default: false },
  desde: { type: String, default: 'notas' },
  clickeable: { type: Boolean, default: false },
})

const hoverId = ref(null)
const router = useRouter()
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100">
    <div class="tabla-header">
      <span class="flex items-center text-left">Número</span>
      <span class="flex items-center text-left">Tema</span>
      <span class="flex items-center text-left">Estado</span>
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
        :class="{ 'tabla-fila--clickeable': clickeable }"
        @mouseenter="hoverId = nota.id"
        @mouseleave="hoverId = null"
        :style="{
          borderLeftColor: hoverId === nota.id ? COLORES_ESTADO[nota.estado] : 'transparent',
        }"
        @click="clickeable ? router.push(`/notas/${nota.id}?desde=${desde}`) : null"
      >
        <span class="font-mono text-sm font-bold text-[#1e3a5f] truncate">
          {{ nota.numero_nota }}
        </span>
        <span class="text-sm text-gray-700 truncate" :title="nota.tema">
          {{ nota.tema }}
        </span>
        <BadgeEstado :estado="nota.estado" />
        <span class="flex justify-end" @click.stop>
          <BtnDetalle :nota-id="nota.id" :desde="desde" />
        </span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.tabla-header {
  display: grid;
  grid-template-columns: 140px 1fr 120px 120px;
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
  grid-template-columns: 140px 1fr 120px 120px;
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
.tabla-fila--clickeable {
  cursor: pointer;
}
</style>
