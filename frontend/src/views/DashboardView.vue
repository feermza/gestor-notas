<script setup>
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div class="p-6">
    <h1 class="text-2xl font-semibold text-gray-800 mb-2">Inicio</h1>
    <p class="text-gray-600 mb-6">
      Bienvenido, <strong>{{ auth.nombreCompleto || auth.usuario?.username }}</strong>.
      <span v-if="auth.rol" class="text-sm text-gray-500">({{ auth.usuario?.rol_display }})</span>
    </p>
    <div
      class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
      style="border-left: 4px solid var(--color-primario)"
    >
      <p class="text-gray-600">
        Panel de control en construcción. Desde aquí accederás a Notas, Pendientes y Atrasadas.
      </p>
    </div>
  </div>
</template>
