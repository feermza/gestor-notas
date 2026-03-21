<template>
  <button
    @click.stop="router.push(`/notas/${notaId}?desde=${desde}`)"
    class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium shrink-0 whitespace-nowrap text-gray-500 bg-white border border-gray-200 hover:bg-[#475569] hover:text-white hover:border-[#475569] active:scale-95 transition-all duration-150 cursor-pointer"
  >
    Ver detalle
    <i class="pi pi-chevron-right text-xs" />
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
defineProps({ notaId: Number, desde: String })
</script>
