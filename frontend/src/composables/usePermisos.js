import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

export function usePermisos() {
  const auth = useAuthStore()

  const rol = computed(() => auth.usuario?.rol ?? null)

  const esSupervisorOAdmin = computed(() =>
    ['SUPERVISOR', 'ADMINISTRADOR'].includes(rol.value)
  )

  const esOperador = computed(() =>
    rol.value === 'OPERADOR'
  )

  const esAdmin = computed(() =>
    rol.value === 'ADMINISTRADOR'
  )

  const esConsultor = computed(() =>
    rol.value === 'CONSULTOR'
  )

  const puedeCrearNota = computed(() =>
    ['ADMINISTRADOR', 'SUPERVISOR', 'OPERADOR'].includes(rol.value)
  )

  const puedeGestionarUsuarios = computed(() =>
    rol.value === 'ADMINISTRADOR'
  )

  const usuarioId = computed(() => auth.usuario?.id)

  function esResponsableDe(nota) {
    if (!nota) return false
    return Number(nota.responsable?.id) === Number(usuarioId.value)
  }

  return {
    rol,
    esSupervisorOAdmin,
    esOperador,
    esAdmin,
    esConsultor,
    puedeCrearNota,
    puedeGestionarUsuarios,
    usuarioId,
    esResponsableDe,
  }
}
