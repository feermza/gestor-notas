import { get, post, patch, postFormData } from '@/api/cliente'

export const notasService = {
  getNotas: (params = '') => get(`/api/notas/${params}`),
  getPendientes: () => get('/api/notas/pendientes/'),
  getAtrasadas: () => get('/api/notas/atrasadas/'),
  getNota: (id) => get(`/api/notas/${id}/`),
  crearNota: (data) => post('/api/notas/', data),
  cambiarEstado: (id, data) => post(`/api/notas/${id}/cambiar_estado/`, data),
  subirAdjunto: (id, formData) => postFormData(`/api/notas/${id}/adjuntos/`, formData),
}

export const sectoresService = {
  /** @param {string} [suffix] ej. '' o '?activos=true' */
  getSectores: (suffix = '') => get(`/api/sectores/${suffix}`),
  crearSector: (data) => post('/api/sectores/', data),
  actualizarSector: (id, data) => patch(`/api/sectores/${id}/`, data),
}

export const usuariosService = {
  getUsuarios: () => get('/api/usuarios/'),
  getUsuariosActivos: () => get('/api/usuarios/activos/'),
  crearUsuario: (data) => post('/api/usuarios/', data),
  actualizarUsuario: (id, data) => patch(`/api/usuarios/${id}/`, data),
}

export const reportesService = {
  getReportesPorSector: () => get('/api/reportes/notas-por-sector/'),
  getReportesPorOperador: () => get('/api/reportes/notas-por-operador/'),
  getAuditoria: () => get('/api/auditoria/'),
}
