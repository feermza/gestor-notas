<template>
  <button
    type="button"
    @click="volver"
    class="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium text-gray-500 bg-white border border-gray-200 shadow-sm hover:bg-[#1e3a5f] hover:text-white hover:border-[#1e3a5f] active:scale-95 transition-all duration-200 cursor-pointer"
  >
    <i class="pi pi-chevron-left text-xs" />
    {{ label }}
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
const props = defineProps({
  label: { type: String, default: 'Volver' },
  destino: { type: String, default: null },
})

function volver() {
  if (props.destino) {
    router.push(props.destino)
  } else {
    router.back()
  }
}
</script>
