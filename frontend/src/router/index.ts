import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';  // replace ".." with "@"

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
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
      component: () => import('@/views/LoginView.vue')
    },
    {
      path: '/sources',
      name: 'sources',
      component: () => import('@/views/SourcesView.vue'),
      meta: { requiresAuth: true }
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

export default router;
