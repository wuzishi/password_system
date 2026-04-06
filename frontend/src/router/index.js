import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/',
    component: () => import('../components/layout/AppLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/DashboardView.vue'),
      },
      {
        path: 'passwords',
        name: 'Passwords',
        component: () => import('../views/PasswordVaultView.vue'),
      },
      {
        path: 'teams',
        name: 'Teams',
        component: () => import('../views/TeamsView.vue'),
      },
      {
        path: 'teams/:id',
        name: 'TeamDetail',
        component: () => import('../views/TeamDetailView.vue'),
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/UsersManageView.vue'),
        meta: { requiredRole: 'admin' },
      },
      {
        path: 'audit',
        name: 'Audit',
        component: () => import('../views/AuditLogView.vue'),
        meta: { requiredRole: 'admin' },
      },
      {
        path: 'approvals',
        name: 'Approvals',
        component: () => import('../views/ApprovalsView.vue'),
      },
      {
        path: 'servers',
        name: 'Servers',
        component: () => import('../views/ServersView.vue'),
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/ProfileView.vue'),
      },
    ],
  },
  {
    path: '/terminal/:id',
    name: 'Terminal',
    component: () => import('../views/TerminalView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.matched.some((r) => r.meta.requiresAuth) && !auth.isLoggedIn) {
    next('/login')
  } else if (to.meta.requiredRole && auth.role !== to.meta.requiredRole) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
