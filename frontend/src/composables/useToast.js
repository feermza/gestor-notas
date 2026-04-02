import { ref } from 'vue'

export function useToast() {
  const mensajeExito = ref('')
  const mostrarExito = ref(false)
  const mensajeError = ref('')
  const mostrarError = ref(false)

  function mostrarToastExito(mensaje, duracion = 3000) {
    mensajeExito.value = mensaje
    mostrarExito.value = true
    setTimeout(() => {
      mostrarExito.value = false
    }, duracion)
  }

  function mostrarToastError(mensaje, duracion = 4000) {
    mensajeError.value = mensaje
    mostrarError.value = true
    setTimeout(() => {
      mostrarError.value = false
    }, duracion)
  }

  return {
    mensajeExito,
    mostrarExito,
    mensajeError,
    mostrarError,
    mostrarToastExito,
    mostrarToastError,
  }
}
