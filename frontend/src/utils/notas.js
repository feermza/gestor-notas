/**
 * Utilidades compartidas para notas (estados, prioridades, formato de fechas).
 * Usado por DashboardView y NotasView.
 */

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
  BAJA: '#cbd5e1',
  NORMAL: '#0ea5e9',
  MEDIA: '#0ea5e9', // API devuelve MEDIA, mismo color que NORMAL
  ALTA: '#f97316',
  URGENTE: '#dc2626',
}

export const LABELS_PRIORIDAD = {
  BAJA: 'Baja',
  NORMAL: 'Normal',
  MEDIA: 'Normal', // API devuelve MEDIA
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
  const d = new Date(fechaStr + 'T12:00:00')
  return d.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/** "hace X minutos", "hace 2 horas", "ayer", "hace 3 días" */
export function haceCuanto(fechaStr) {
  if (!fechaStr) return '—'
  const fecha = new Date(fechaStr + 'T12:00:00')
  const ahora = new Date()
  const diffMs = ahora - fecha
  const diffDias = Math.floor(diffMs / (24 * 60 * 60 * 1000))
  const diffHoras = Math.floor(diffMs / (60 * 60 * 1000))
  const diffMin = Math.floor(diffMs / (60 * 1000))

  if (diffMin < 60)
    return diffMin <= 1 ? 'hace un momento' : `hace ${diffMin} minutos`
  if (diffHoras < 24)
    return diffHoras === 1 ? 'hace 1 hora' : `hace ${diffHoras} horas`
  if (diffDias === 1) return 'ayer'
  if (diffDias < 7) return `hace ${diffDias} días`
  return formatoFecha(fechaStr)
}

export function colorEstado(estado) {
  return COLORES_ESTADO[estado] || '#64748b'
}

export function labelEstado(estado) {
  return LABELS_ESTADO[estado] || estado || '—'
}

export function colorPrioridad(prioridad) {
  return COLORES_PRIORIDAD[prioridad] || '#cbd5e1'
}

export function labelPrioridad(prioridad) {
  return LABELS_PRIORIDAD[prioridad] || prioridad || '—'
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
  const d = new Date(fechaStr + 'T12:00:00')
  const hoy = new Date()
  return d.getFullYear() === hoy.getFullYear() && d.getMonth() === hoy.getMonth()
}

/** Devuelve true si fecha_ingreso es hoy */
export function esHoy(fechaStr) {
  if (!fechaStr) return false
  const d = new Date(fechaStr + 'T12:00:00')
  const hoy = new Date()
  return (
    d.getFullYear() === hoy.getFullYear() &&
    d.getMonth() === hoy.getMonth() &&
    d.getDate() === hoy.getDate()
  )
}
