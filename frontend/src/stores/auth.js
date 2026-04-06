import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, logout as logoutApi } from '../api/auth'
import { usePermissionStore } from './permission'
import { useDecryptStore } from './decrypt'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const role = ref(localStorage.getItem('role') || '')
  const userId = ref(parseInt(localStorage.getItem('userId') || '0'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'admin')

  async function login(credentials) {
    const { data } = await loginApi(credentials)
    token.value = data.access_token
    refreshToken.value = data.refresh_token || ''
    username.value = data.username
    role.value = data.role
    userId.value = data.user_id
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token || '')
    localStorage.setItem('username', data.username)
    localStorage.setItem('role', data.role)
    localStorage.setItem('userId', data.user_id)
    const permStore = usePermissionStore()
    await permStore.load()
  }

  function setTokens(access, refresh) {
    token.value = access
    refreshToken.value = refresh
    localStorage.setItem('token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  async function logout() {
    try { await logoutApi() } catch {}
    token.value = ''
    refreshToken.value = ''
    username.value = ''
    role.value = ''
    userId.value = 0
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
    localStorage.removeItem('userId')
    const permStore = usePermissionStore()
    permStore.clear()
    const decryptStore = useDecryptStore()
    decryptStore.clearToken()
  }

  return { token, refreshToken, username, role, userId, isLoggedIn, isAdmin, login, logout, setTokens }
})
