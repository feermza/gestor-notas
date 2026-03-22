<template>
  <span
    :style="{ backgroundColor: color }"
    style="display: inline-flex; align-items: center;
           width: fit-content; max-width: fit-content;
           padding: 2px 10px; border-radius: 9999px;
           font-size: 12px; font-weight: 500;
           color: white; white-space: nowrap;">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { COLORES_ESTADO, LABELS_ESTADO } from '@/utils/notas'

const props = defineProps({
  estado: { type: String, required: true }
})

const color = computed(() => COLORES_ESTADO[props.estado] || '#475569')
const label = computed(() => LABELS_ESTADO[props.estado] || props.estado)
</script>
