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
import { COLORES_PRIORIDAD, LABELS_PRIORIDAD } from '@/utils/notas'

const props = defineProps({
  prioridad: { type: String, required: true }
})

const color = computed(() => COLORES_PRIORIDAD[props.prioridad] || '#475569')
const label = computed(() => LABELS_PRIORIDAD[props.prioridad] || props.prioridad)
</script>
