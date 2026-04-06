import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { usePermissionStore } from '../stores/permission'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/accept-invite',
    name: 'AcceptInvite',
    component: () => import('../views/AcceptInviteView.vue'),
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
        meta: { permKey: 'page.dashboard' },
      },
      {
        path: 'passwords',
        name: 'Passwords',
        component: () => import('../views/PasswordVaultView.vue'),
        meta: { permKey: 'page.passwords' },
      },
      {
        path: 'teams',
        name: 'Teams',
        component: () => import('../views/TeamsView.vue'),
        meta: { permKey: 'page.teams' },
      },
      {
        path: 'teams/:id',
        name: 'TeamDetail',
        component: () => import('../views/TeamDetailView.vue'),
        meta: { permKey: 'page.teams' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/UsersManageView.vue'),
        meta: { permKey: 'page.users' },
      },
      {
        path: 'audit',
        name: 'Audit',
        component: () => import('../views/AuditLogView.vue'),
        meta: { permKey: 'page.audit' },
      },
      {
        path: 'approvals',
        name: 'Approvals',
        component: () => import('../views/ApprovalsView.vue'),
        meta: { permKey: 'page.approvals' },
      },
      {
        path: 'servers',
        name: 'Servers',
        component: () => import('../views/ServersView.vue'),
        meta: { permKey: 'page.servers' },
      },
      {
        path: 'permissions',
        name: 'Permissions',
        component: () => import('../views/PermissionsView.vue'),
        meta: { permKey: 'page.permissions' },
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

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  const perm = usePermissionStore()

  // Public pages
  if (!to.matched.some((r) => r.meta.requiresAuth) && !to.meta.permKey) {
    next()
    return
  }

  // Not logged in
  if (!auth.isLoggedIn) {
    next('/login')
    return
  }

  // Load permissions if not yet loaded
  if (!perm.loaded) {
    await perm.load()
  }

  // Check page permission
  if (to.meta.permKey && !perm.has(to.meta.permKey)) {
    // Redirect to first accessible page
    const fallback = ['/dashboard', '/passwords', '/servers', '/approvals'].find(
      (p) => perm.has(`page.${p.slice(1)}`)
    )
    next(fallback || '/profile')
    return
  }

  next()
})

export default router
