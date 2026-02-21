/**
 * Cliente HTTP para la API del backend Django.
 * Usa fetch nativo con credentials para enviar cookies de sesión.
 * En desarrollo el proxy de Vite redirige /api a http://127.0.0.1:8000.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

/**
 * Obtiene el token CSRF de la cookie (Django lo envía como csrftoken).
 * Necesario para POST/PATCH/DELETE cuando se usa SessionAuthentication.
 */
function getCsrfToken() {
  const name = 'csrftoken'
  const cookies = document.cookie.split(';')
  for (let i = 0; i < cookies.length; i++) {
    const c = cookies[i].trim()
    if (c.startsWith(name + '=')) return c.substring(name.length + 1)
  }
  return null
}

/**
 * Realiza una petición HTTP.
 * NO redirige automáticamente en 401 - eso lo maneja el router guard.
 * @param {string} url - URL relativa (ej: '/api/auth/login/')
 * @param {RequestInit} options - Opciones de fetch
 * @returns {Promise<Response>}
 */
async function request(url, options = {}) {
  const fullUrl = url.startsWith('http') ? url : `${BASE_URL}${url}`
  const method = (options.method || 'GET').toUpperCase()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  const csrf = getCsrfToken()
  if (csrf && method !== 'GET') headers['X-CSRFToken'] = csrf
  const config = {
    ...options,
    credentials: 'include',
    headers,
  }
  const response = await fetch(fullUrl, config)
  // No redirigir aquí - el router guard maneja los 401
  return response
}

/**
 * Parsea respuesta JSON o lanza con mensaje del backend.
 * @param {Response} response
 * @returns {Promise<object>}
 */
async function parseJson(response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const err = new Error(data.error || data.detalle || 'Error en la petición')
    err.data = data
    throw err
  }
  return data
}

/**
 * GET
 * @param {string} url
 * @returns {Promise<object>} JSON
 */
export async function get(url) {
  const response = await request(url, { method: 'GET' })
  if (response.headers.get('content-type')?.includes('application/json')) {
    return parseJson(response)
  }
  return response
}

/**
 * POST
 * @param {string} url
 * @param {object} data - Cuerpo JSON
 * @returns {Promise<object>} JSON
 */
export async function post(url, data) {
  const response = await request(url, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  })
  if (response.headers.get('content-type')?.includes('application/json')) {
    return parseJson(response)
  }
  return response
}

/**
 * PATCH
 * @param {string} url
 * @param {object} data - Cuerpo JSON
 * @returns {Promise<object>} JSON
 */
export async function patch(url, data) {
  const response = await request(url, {
    method: 'PATCH',
    body: data ? JSON.stringify(data) : undefined,
  })
  if (response.headers.get('content-type')?.includes('application/json')) {
    return parseJson(response)
  }
  return response
}

/**
 * DELETE
 * @param {string} url
 * @returns {Promise<Response>}
 */
export async function del(url) {
  return request(url, { method: 'DELETE' })
}
