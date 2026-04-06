import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const role = ref(localStorage.getItem('role') || '')
  const userId = ref(parseInt(localStorage.getItem('userId') || '0'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'admin')
  const isProduct = computed(() => role.value === 'product')
  const isDeveloper = computed(() => role.value === 'developer')

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
  }

  return { token, username, role, userId, isLoggedIn, isAdmin, isProduct, isDeveloper, login, logout }
})
