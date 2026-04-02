import { ref } from 'vue'
import { toArray } from '@/utils/notas'
import { get } from '@/api/cliente'

export function useNotas() {
  const notas = ref([])
  const cargando = ref(false)
  const error = ref(null)

  async function cargarNotas(params = '') {
    cargando.value = true
    error.value = null
    try {
      const res = await get(`/api/notas/${params}`)
      notas.value = toArray(res)
    } catch (e) {
      error.value =
        e?.data?.detalle || e?.data?.error || e?.message || 'Error al cargar notas.'
    } finally {
      cargando.value = false
    }
  }

  async function cargarPendientes() {
    cargando.value = true
    error.value = null
    try {
      const res = await get('/api/notas/pendientes/')
      notas.value = toArray(res)
    } catch (e) {
      error.value =
        e?.data?.detalle || e?.data?.error || e?.message || 'Error al cargar notas.'
      notas.value = []
    } finally {
      cargando.value = false
    }
  }

  return {
    notas,
    cargando,
    error,
    cargarNotas,
    cargarPendientes,
  }
}
