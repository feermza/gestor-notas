import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import LoginNuevo from '@/views/LoginNuevo.vue'
import DashboardView from '@/views/DashboardView.vue'
import MainLayout from '@/layouts/MainLayout.vue'
// NotasView se carga con lazy loading

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },

    {
      path: '/login-test',
      name: 'login-test',
      component: LoginNuevo,
      meta: { public: true },
    },

    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: DashboardView,
        },
        // Listado de notas
        {
          path: 'notas',
          name: 'notas',
          component: () => import('@/views/NotasView.vue'),
        },
        // Detalle de nota
        {
          path: 'notas/:id',
          name: 'nota-detalle',
          component: () => import('@/views/NotaDetalleView.vue'),
        },
        {
          path: 'notas/nueva',
          name: 'notas-nueva',
          component: () => import('@/views/NuevaNotaView.vue'),
        },
        {
          path: 'notas/pendientes',
          name: 'notas-pendientes',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'notas/atrasadas',
          name: 'notas-atrasadas',
          component: () => import('@/views/DashboardView.vue'),
        },
      ],
    },
  ],
})

// Guardia de navegación: requiere auth o redirige a login
router.beforeEach(async (to, from) => {
  const authStore = useAuthStore()

  // Si la ruta es pública (/login)
  if (to.meta.public) {
    // Si ya está logueado, redirigir al dashboard
    if (authStore.estaLogueado) {
      return '/'
    }
    return true
  }

  // Si la ruta requiere autenticación
  if (to.meta.requiresAuth) {
    // Si no hay usuario en el store, intentar cargarlo desde el backend
    if (!authStore.usuario) {
      await authStore.cargarUsuario()
    }

    // Si después de cargarUsuario() sigue sin haber usuario, redirigir a login
    if (!authStore.usuario) {
      return '/login'
    }
  }

  // Permitir acceso
  return true
})

export default router
