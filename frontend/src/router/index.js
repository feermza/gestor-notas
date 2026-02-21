import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import MainLayout from '@/layouts/MainLayout.vue'

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
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: DashboardView,
        },
        // Placeholder para rutas futuras (Notas, Pendientes, Atrasadas)
        {
          path: 'notas',
          name: 'notas',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'notas/nueva',
          name: 'notas-nueva',
          component: () => import('@/views/DashboardView.vue'),
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
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Si la ruta es pública (/login)
  if (to.meta.public) {
    // Si ya está logueado, redirigir al dashboard
    if (authStore.estaLogueado) {
      return next('/')
    }
    return next()
  }

  // Si la ruta requiere autenticación
  if (to.meta.requiresAuth) {
    // Si no hay usuario en el store, intentar cargarlo desde el backend
    if (!authStore.usuario) {
      await authStore.cargarUsuario()
    }

    // Si después de cargarUsuario() sigue sin haber usuario, redirigir a login
    if (!authStore.usuario) {
      return next('/login')
    }
  }

  // Permitir acceso
  next()
})

export default router
