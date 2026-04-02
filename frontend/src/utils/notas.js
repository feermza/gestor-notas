/**
 * Utilidades compartidas para notas (estados, prioridades, formato de fechas).
 * Usado por DashboardView y NotasView.
 */

/** Normaliza respuestas paginadas de la API a un array. */
export function toArray(res) {
  return Array.isArray(res) ? res : res?.results || []
}

// Colores de estado para Tags (según especificación)
export const COLORES_ESTADO = {
  INGRESADA: '#475569',
  EN_REVISION: '#0891b2',
  ASIGNADA: '#6366f1',
  EN_PROCESO: '#1d4ed8',
  EN_ESPERA: '#d97706',
  DEVUELTA: '#e11d48',
  RESUELTA: '#059669',
  ARCHIVADA: '#94a3b8',
  ANULADA: '#450a0a',
}

export const LABELS_ESTADO = {
  INGRESADA: 'Ingresada',
  EN_REVISION: 'En Revisión',
  ASIGNADA: 'Asignada',
  EN_PROCESO: 'En Proceso',
  EN_ESPERA: 'En Espera',
  DEVUELTA: 'Devuelta',
  RESUELTA: 'Resuelta',
  ARCHIVADA: 'Archivada',
  ANULADA: 'Anulada',
}

// Colores y etiquetas para prioridad (BAJA, NORMAL/MEDIA, ALTA, URGENTE)
export const COLORES_PRIORIDAD = {
  BAJA: '#64748b',
  NORMAL: '#0ea5e9',
  MEDIA: '#0ea5e9', // API devuelve MEDIA, mismo color que NORMAL
  ALTA: '#f97316',
  URGENTE: '#dc2626',
}

export const LABELS_PRIORIDAD = {
  BAJA: 'Baja',
  NORMAL: 'Normal',
  MEDIA: 'Normal',
  ALTA: 'Alta',
  URGENTE: 'Urgente',
}

/** Trunca texto a max caracteres con ellipsis */
export function truncar(texto, max = 40) {
  if (!texto) return ''
  return texto.length <= max ? texto : texto.slice(0, max) + '…'
}

/** Formato corto de fecha (dd/mm/yyyy) */
export function formatoFecha(fechaStr) {
  if (!fechaStr) return '—'
  const fechaLimpia = fechaStr.replace(/(\.\d{3})\d+/, '$1')
  const d = new Date(fechaLimpia)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/** Formato fecha y hora (dd/mm/yyyy HH:MM) */
export function formatoFechaHora(fechaStr) {
  if (!fechaStr) return '—'
  const fechaLimpia = fechaStr.replace(/(\.\d{3})\d+/, '$1')
  const d = new Date(fechaLimpia)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** "hace X minutos", "hace 2 horas", "ayer", "hace 3 días" */
export function haceCuanto(fechaStr) {
  if (!fechaStr) return '—'
  // Limpiar microsegundos que algunos navegadores no parsean
  const fechaLimpia = fechaStr.replace(/(\.\d{3})\d+/, '$1')
  const fecha = new Date(fechaLimpia)
  if (isNaN(fecha.getTime())) return '—'
  const ahora = new Date()
  const diffMs = ahora - fecha
  const diffDias = Math.floor(diffMs / (24 * 60 * 60 * 1000))
  const diffHoras = Math.floor(diffMs / (60 * 60 * 1000))
  const diffMin = Math.floor(diffMs / (60 * 1000))

  if (diffMin < 60) return diffMin <= 1 ? 'hace un momento' : `hace ${diffMin} minutos`
  if (diffHoras < 24) return diffHoras === 1 ? 'hace 1 hora' : `hace ${diffHoras} horas`
  if (diffDias === 1) return 'ayer'
  if (diffDias < 7) return `hace ${diffDias} días`
  return formatoFecha(fechaStr)
}

/** Devuelve true si fecha_limite está en el pasado y la nota no está archivada/anulada */
export function esAtrasada(nota) {
  if (!nota?.fecha_limite) return false
  if (['ARCHIVADA', 'ANULADA'].includes(nota.estado)) return false
  const hoy = new Date().toISOString().slice(0, 10)
  return nota.fecha_limite < hoy
}

/** Devuelve true si fecha_ingreso está en el mes actual */
export function esDelMesActual(fechaStr) {
  if (!fechaStr) return false
  const fechaLimpia = fechaStr.replace(/(\.\d{3})\d+/, '$1')
  const d = new Date(fechaLimpia)
  if (isNaN(d.getTime())) return false
  const hoy = new Date()
  return d.getFullYear() === hoy.getFullYear() && d.getMonth() === hoy.getMonth()
}

/** Milisegundos desde epoch para fecha_ingreso (más reciente = mayor). */
export function fechaIngresoMs(nota) {
  const s = typeof nota === 'string' ? nota : nota?.fecha_ingreso
  if (!s) return 0
  const fechaLimpia = String(s).replace(/(\.\d{3})\d+/, '$1')
  const t = new Date(fechaLimpia).getTime()
  return Number.isNaN(t) ? 0 : t
}

/** Orden descendente por fecha de ingreso (alineado con API -fecha_ingreso). */
export function compareFechaIngresoDesc(a, b) {
  return fechaIngresoMs(b) - fechaIngresoMs(a)
}

/** Prioridad más urgente primero; luego fecha de ingreso descendente. */
export function ordenarPorPrioridadYFecha(notas) {
  const ORDEN = { URGENTE: 0, ALTA: 1, NORMAL: 2, MEDIA: 2, BAJA: 3 }
  return [...notas].sort((a, b) => {
    const pa = ORDEN[a.prioridad] ?? 4
    const pb = ORDEN[b.prioridad] ?? 4
    if (pa !== pb) return pa - pb
    const fa = new Date((a.fecha_ingreso || '').replace(/(\.\d{3})\d+/, '$1'))
    const fb = new Date((b.fecha_ingreso || '').replace(/(\.\d{3})\d+/, '$1'))
    return fb - fa
  })
}

/** URGENTE primero; el resto por fecha de ingreso descendente (panel operador). */
export function ordenarPendientesOperador(notas) {
  return [...notas].sort((a, b) => {
    const aUrgente = a.prioridad === 'URGENTE' ? 0 : 1
    const bUrgente = b.prioridad === 'URGENTE' ? 0 : 1
    if (aUrgente !== bUrgente) return aUrgente - bUrgente
    const fa = new Date((a.fecha_ingreso || '').replace(/(\.\d{3})\d+/, '$1'))
    const fb = new Date((b.fecha_ingreso || '').replace(/(\.\d{3})\d+/, '$1'))
    return fb - fa
  })
}

/**
 * Acciones de detalle de nota por estado, rol y si el usuario es el responsable.
 * @returns {{ habilitadas: string[], deshabilitadas: { accion: string, motivo: string }[] }}
 */
export function accionesDisponibles(estado, rol, esResponsable) {
  const esSuperAdmin = ['SUPERVISOR', 'ADMINISTRADOR'].includes(rol)

  const habilitadas = []
  const deshabilitadas = []

  if (esResponsable || esSuperAdmin) {
    switch (estado) {
      case 'INGRESADA':
        if (esSuperAdmin) {
          habilitadas.push('asignar', 'devuelta', 'archivar')
          deshabilitadas.push({
            accion: 'reasignar',
            motivo: 'Solo disponible desde Asignada, En Proceso o En Espera',
          })
        }
        break

      case 'ASIGNADA':
        if (esResponsable) {
          habilitadas.push('iniciar')
          deshabilitadas.push(
            { accion: 'resuelta', motivo: 'Solo disponible desde En Proceso' },
            { accion: 'en_espera', motivo: 'Solo disponible desde En Proceso' },
            { accion: 'archivar', motivo: 'Solo disponible desde Resuelta' },
          )
        }
        if (esSuperAdmin) {
          habilitadas.push('reasignar', 'devuelta', 'archivar')
        }
        break

      case 'EN_PROCESO':
        if (esResponsable) {
          habilitadas.push('resuelta', 'en_espera')
          deshabilitadas.push(
            { accion: 'iniciar', motivo: 'El proceso ya fue iniciado' },
            { accion: 'archivar', motivo: 'Solo disponible desde Resuelta' },
          )
        }
        if (esSuperAdmin) {
          habilitadas.push('reasignar', 'devuelta', 'archivar')
        }
        break

      case 'EN_ESPERA':
        if (esResponsable) {
          habilitadas.push('retomar')
          deshabilitadas.push(
            { accion: 'resuelta', motivo: 'Debés retomar el proceso primero' },
            { accion: 'archivar', motivo: 'Solo disponible desde Resuelta' },
          )
        }
        if (esSuperAdmin) {
          habilitadas.push('reasignar', 'devuelta', 'archivar')
        }
        break

      case 'RESUELTA':
        habilitadas.push('archivar')
        if (esSuperAdmin) {
          deshabilitadas.push(
            { accion: 'reasignar', motivo: 'No disponible en estado Resuelta' },
            { accion: 'devuelta', motivo: 'No disponible en estado Resuelta' },
          )
        }
        break
    }
  }

  return { habilitadas, deshabilitadas }
}
