import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/',
      name: 'tickets',
      component: () => import('../views/TicketTableView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/tickets/:id',
      name: 'ticket-detail',
      component: () => import('../views/TicketDetailView.vue'),
      meta: { requiresAuth: true },
      props: true,
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'tickets' }
  }
})

export default router
