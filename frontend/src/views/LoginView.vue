<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { get } from '@/api/cliente'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const enviando = ref(false)

// Una petición GET al backend hace que Django envíe la cookie CSRF (necesaria para el POST de login)
onMounted(() => {
  get('/api/usuarios/yo/').catch(() => {})
})

const mensajeError = computed(() => auth.error)

async function enviar() {
  if (!username.value.trim() || !password.value) return
  enviando.value = true
  auth.error = null
  try {
    await auth.login(username.value.trim(), password.value)
    router.push('/')
  } catch (e) {
    // Error ya guardado en auth.error
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div
    class="min-h-screen flex items-center justify-center px-4"
    style="background: linear-gradient(135deg, var(--color-primario) 0%, var(--color-secundario) 100%)"
  >
    <div class="w-full max-w-md">
      <!-- Tarjeta de login -->
      <div class="bg-white rounded-2xl shadow-2xl overflow-hidden">
        <!-- Cabecera institucional -->
        <div
          class="py-8 px-6 text-center text-white"
          style="background: linear-gradient(180deg, var(--color-primario) 0%, #254a75 100%)"
        >
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 bg-white/20">
            <i class="pi pi-folder text-3xl"></i>
          </div>
          <h1 class="text-2xl font-bold tracking-tight">Gestor de Notas</h1>
          <p class="text-sm opacity-90 mt-1">Recursos Humanos</p>
        </div>

        <form class="p-8 space-y-5" @submit.prevent="enviar">
          <div>
            <label for="username" class="block text-sm font-medium text-gray-700 mb-1">
              Usuario
            </label>
            <InputText
              id="username"
              v-model="username"
              type="text"
              class="w-full"
              placeholder="Nombre de usuario"
              autocomplete="username"
              :disabled="enviando"
            />
          </div>
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <Password
              id="password"
              v-model="password"
              class="w-full"
              placeholder="Contraseña"
              :feedback="false"
              toggle-mask
              input-class="w-full"
              :disabled="enviando"
            />
          </div>

          <div v-if="mensajeError" class="p-3 rounded-lg bg-red-50 text-red-700 text-sm">
            {{ mensajeError }}
          </div>

          <Button
            type="submit"
            label="Ingresar"
            icon="pi pi-sign-in"
            class="w-full justify-center"
            :loading="enviando"
            :disabled="!username.trim() || !password"
            style="background: var(--color-primario); border-color: var(--color-primario)"
          />
        </form>
      </div>

      <p class="text-center text-white/80 text-sm mt-6">
        Sistema de gestión y seguimiento de notas
      </p>
    </div>
  </div>
</template>
