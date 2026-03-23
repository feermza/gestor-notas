<script setup>
import NuevaNotaModal from '@/components/NuevaNotaModal.vue'
</script>

<template>
  <div class="nueva-nota min-h-full" style="background-color: #eef2f7">
    <div class="p-4 md:p-6 max-w-4xl mx-auto">
      <header class="mb-6">
        <h1 class="text-2xl md:text-3xl font-bold text-[#1e3a5f]">Nueva nota</h1>
        <p class="text-gray-600 mt-1">Completá los datos de la nota</p>
      </header>
      <NuevaNotaModal embed-page />
    </div>
  </div>
</template>

<style scoped>
.nueva-nota {
  min-height: 100%;
}
</style>
