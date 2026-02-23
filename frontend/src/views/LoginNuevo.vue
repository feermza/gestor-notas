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
  } catch {
    // Error ya guardado en auth.error
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div class="login-screen">
    <div class="login-screen-inner flex items-center justify-center px-4 min-h-screen">
      <div class="w-full max-w-md">
        <!-- Tarjeta glassmorphism -->
        <div class="login-card">
          <!-- Header integrado -->
          <header class="login-card-header">
            <div class="login-icon-wrap">
              <i class="pi pi-folder text-3xl text-[#1e3a5f]"></i>
            </div>
            <h1 class="login-title">Gestor de Notas</h1>
            <p class="login-subtitle">Sistema de Gestión y Seguimiento</p>
          </header>

          <form class="login-form" @submit.prevent="enviar">
            <div class="login-field">
              <label for="username" class="login-label">Usuario</label>
              <InputText
                id="username"
                v-model="username"
                type="text"
                class="w-full login-input"
                placeholder="Nombre de usuario"
                autocomplete="username"
                :disabled="enviando"
              />
            </div>
            <div class="login-field">
              <label for="password" class="login-label">Contraseña</label>
              <Password
                id="password"
                v-model="password"
                class="w-full login-input"
                placeholder="Contraseña"
                :feedback="false"
                toggle-mask
                input-class="w-full"
                :disabled="enviando"
              />
            </div>

            <div v-if="mensajeError" class="login-error">
              {{ mensajeError }}
            </div>

            <Button
              type="submit"
              label="Ingresar"
              icon="pi pi-arrow-right"
              icon-pos="right"
              class="login-btn w-full justify-center"
              :loading="enviando"
              :disabled="!username.trim() || !password"
            />
          </form>
        </div>

        <footer class="login-footer">
          © 2026 Dirección de Recursos Humanos — UTN Facultad Regional Mendoza
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 1. FONDO: imagen o degradado + overlay */
.login-screen {
  min-height: 100vh;
  background-color: #1a2f4a;
  background-image:
    linear-gradient(135deg, rgba(15, 30, 50, 0.65) 0%, rgba(15, 30, 50, 0.65) 100%),
    url('/images/institucional.jpg'), linear-gradient(135deg, #1a2f4a 0%, #2d5986 50%, #1a2f4a 100%);
  background-size: cover;
  background-position: center;
}

.login-screen-inner {
  min-height: 100vh;
}

/* 2. TARJETA glassmorphism */
.login-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 1.5rem;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

/* 3. HEADER */
.login-card-header {
  padding: 2rem 2rem 0.5rem;
  text-align: center;
}

.login-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 4rem;
  height: 4rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  margin-bottom: 1rem;
}

.login-title {
  color: #fff;
  font-weight: 700;
  font-size: 1.25rem;
  line-height: 1.75rem;
  margin: 0;
}

.login-subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.875rem;
  margin: 0.25rem 0 0;
}

/* 4–5. FORM, LABELS, CAMPOS */
.login-form {
  padding: 1.5rem 2rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.login-label {
  color: rgba(255, 255, 255, 0.85);
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Inputs: fondo casi blanco, texto oscuro, borde claro */
:deep(.login-input.p-inputtext),
:deep(.login-input .p-inputtext),
:deep(.p-password input) {
  background: rgba(255, 255, 255, 0.9) !important;
  color: #1e293b !important;
  border: 1px solid rgba(255, 255, 255, 0.4) !important;
  border-radius: 0.75rem !important;
}
:deep(.login-input.p-inputtext::placeholder),
:deep(.login-input .p-inputtext::placeholder),
:deep(.p-password input::placeholder) {
  color: #94a3b8 !important;
}
:deep(.p-password .p-inputtext) {
  border-radius: 0.75rem !important;
}
:deep(.login-input.p-inputtext:enabled:hover),
:deep(.login-input .p-inputtext:enabled:hover),
:deep(.p-password input:enabled:hover) {
  border-color: rgba(255, 255, 255, 0.5) !important;
}
:deep(.login-input.p-inputtext:enabled:focus),
:deep(.login-input .p-inputtext:enabled:focus),
:deep(.p-password.p-inputtext:focus-within input),
:deep(.p-password input:enabled:focus) {
  border-color: rgba(255, 255, 255, 0.6) !important;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.2) !important;
  outline: none !important;
}

.login-error {
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  background: rgba(254, 226, 226, 0.95);
  color: #b91c1c;
  font-size: 0.875rem;
}

/* 6. BOTÓN INGRESAR */
.login-btn {
  background: #1e3a5f !important;
  border: none !important;
  color: #fff !important;
  font-weight: 700 !important;
  letter-spacing: 0.1em !important;
  padding: 0.75rem 1.5rem !important;
  border-radius: 0.75rem !important;
  transition:
    background 0.2s,
    transform 0.2s !important;
}
.login-btn:not(.p-disabled) :deep(.p-button .p-button-icon) {
  color: #fff !important;
}
.login-btn:not(.p-disabled) :deep(.p-button:hover) {
  background: #2d6a9f !important;
  transform: translateY(-1px);
}
.login-btn:not(.p-disabled) :deep(.p-button:hover .p-button-icon) {
  color: #fff !important;
}

/* 7. FOOTER */
.login-footer {
  margin-top: 1.5rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.75);
  font-size: 0.75rem;
  line-height: 1.25rem;
}
</style>
