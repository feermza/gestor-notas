import { ref } from 'vue'

export function useModal() {
  const visible = ref(false)
  const datos = ref(null)

  function abrir(data = null) {
    datos.value = data
    visible.value = true
  }

  function cerrar() {
    visible.value = false
    datos.value = null
  }

  return { visible, datos, abrir, cerrar }
}
