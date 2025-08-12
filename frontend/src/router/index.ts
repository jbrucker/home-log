import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';  // replace ".." with "@"
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'default',
      // if logged in, show user's sources otherwise show login page
      redirect: (to) => {
        const authStore = useAuthStore()
        return authStore.isAuthenticated ? '/sources' : '/login'
      }
    },
    {
      path: '/home',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true }
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/sources',
      name: 'sources',
      component: () => import('@/views/SourcesView.vue'),
      meta: { requiresAuth: true } // Protected route
    },
    {
      path: '/sources/:id/readings',
      name: 'readings',
      component: () => import('@/views/ReadingsView.vue'),
      meta: { requiresAuth: true },
      props: true  // Pass route params as props
    }
  ],
});

// Enhanced authentication check
router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  
  // Skip auth check for non-protected routes
  if (!to.meta.requiresAuth) return true  // ← Better than checking route name
  
  // Validate token for protected routes
  const isValid = await authStore.validateToken()
  if (!isValid) return '/login'
  
  // Optional: Redirect authenticated users away from auth pages (e.g., login/register)
  if (to.meta.redirectIfAuthenticated && authStore.isAuthenticated) {
    return '/'  // Or your default post-login route
  }
})

export default router;
