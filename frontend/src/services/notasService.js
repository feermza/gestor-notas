import { get, post, patch } from '@/api/cliente'

export const notasService = {
  getNotas: (params = '') => get(`/api/notas/${params}`),
  getPendientes: () => get('/api/notas/pendientes/'),
  getAtrasadas: () => get('/api/notas/atrasadas/'),
  getNota: (id) => get(`/api/notas/${id}/`),
  crearNota: (data) => post('/api/notas/', data),
  cambiarEstado: (id, data) => post(`/api/notas/${id}/cambiar_estado/`, data),
  subirAdjunto: (id, formData) => post(`/api/notas/${id}/adjuntos/`, formData),
}

export const sectoresService = {
  getSectores: () => get('/api/sectores/'),
  crearSector: (data) => post('/api/sectores/', data),
  actualizarSector: (id, data) => patch(`/api/sectores/${id}/`, data),
}

export const usuariosService = {
  getUsuarios: () => get('/api/usuarios/'),
  getUsuariosActivos: () => get('/api/usuarios/activos/'),
  crearUsuario: (data) => post('/api/usuarios/', data),
  actualizarUsuario: (id, data) => patch(`/api/usuarios/${id}/`, data),
}
