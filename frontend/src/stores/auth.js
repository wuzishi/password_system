import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi } from '../api/auth'
import { usePermissionStore } from './permission'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const role = ref(localStorage.getItem('role') || '')
  const userId = ref(parseInt(localStorage.getItem('userId') || '0'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'admin')

  async function login(credentials) {
    const { data } = await loginApi(credentials)
    token.value = data.access_token
    username.value = data.username
    role.value = data.role
    userId.value = data.user_id
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    localStorage.setItem('role', data.role)
    localStorage.setItem('userId', data.user_id)
    // Load permissions after login
    const permStore = usePermissionStore()
    await permStore.load()
  }

  function logout() {
    token.value = ''
    username.value = ''
    role.value = ''
    userId.value = 0
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
    localStorage.removeItem('userId')
    const permStore = usePermissionStore()
    permStore.clear()
  }

  return { token, username, role, userId, isLoggedIn, isAdmin, login, logout }
})
