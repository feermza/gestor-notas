import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

export function useFiltrosNotas() {
  const route = useRoute()
  const textoBusqueda = ref('')
  const filtroEstado = ref('')
  const filtroPrioridad = ref('')
  const soloAtrasadas = ref(false)
  const sinAsignar = ref(false)

  const filtroEstadoBloqueado = computed(
    () =>
      !!(
        route.query.estado ||
        route.query.sin_asignar ||
        route.query.atrasadas
      ),
  )

  const vieneDelDashboard = computed(() => filtroEstadoBloqueado.value)

  function aplicarQueryParams() {
    const q = route.query
    filtroEstado.value = ''
    filtroPrioridad.value = ''
    soloAtrasadas.value = false
    sinAsignar.value = false
    textoBusqueda.value = ''
    if (q.estado) filtroEstado.value = q.estado
    if (q.prioridad) filtroPrioridad.value = q.prioridad
    if (q.atrasadas === 'true') soloAtrasadas.value = true
    if (q.sin_asignar === 'true') sinAsignar.value = true
    if (q.search) textoBusqueda.value = q.search
  }

  function limpiarFiltros() {
    textoBusqueda.value = ''
    if (!filtroEstadoBloqueado.value) {
      filtroEstado.value = ''
    }
    filtroPrioridad.value = ''
    soloAtrasadas.value = false
    sinAsignar.value = false
  }

  return {
    textoBusqueda,
    filtroEstado,
    filtroPrioridad,
    soloAtrasadas,
    sinAsignar,
    filtroEstadoBloqueado,
    vieneDelDashboard,
    aplicarQueryParams,
    limpiarFiltros,
  }
}
