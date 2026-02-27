import { defineStore } from 'pinia'
import { get, post } from '@/api/cliente'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    usuario: null,
    cargando: false,
    error: null,
  }),

  getters: {
    estaLogueado: (state) => !!state.usuario,
    nombreCompleto: (state) => state.usuario?.nombre_completo || '',
    rol: (state) => state.usuario?.rol || null,
  },

  actions: {
    async login(legajo, password) {
      this.cargando = true
      this.error = null
      try {
        const data = await post('/api/auth/login/', { legajo, password })
        this.usuario = data.usuario
        return data
      } catch (err) {
        this.error = err.data?.error || err.data?.detalle || err.message || 'Error al iniciar sesión'
        throw err
      } finally {
        this.cargando = false
      }
    },

    async logout() {
      this.cargando = true
      this.error = null
      try {
        await post('/api/auth/logout/')
      } finally {
        this.usuario = null
        this.cargando = false
      }
    },

    async cargarUsuario() {
      this.cargando = true
      this.error = null
      try {
        const data = await get('/api/usuarios/yo/')
        this.usuario = data
        return data
      } catch (err) {
        // Si es 401 o cualquier error, establecer usuario = null
        // NO redirigir desde aquí - eso lo maneja el router guard
        this.usuario = null
        // No lanzar el error, solo actualizar el estado
        return null
      } finally {
        this.cargando = false
      }
    },
  },
})
