import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

let isRefreshing = false
let pendingRequests = []

function _forceLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  localStorage.removeItem('userId')
  router.push('/login')
  ElMessage.error('登录已过期，请重新登录')
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config
    const msg = err.response?.data?.detail || '请求失败'

    if (err.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !originalRequest.url?.includes('/auth/refresh')) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            pendingRequests.push({ resolve, reject })
          }).then(() => {
            originalRequest._retry = true
            originalRequest.headers.Authorization = `Bearer ${localStorage.getItem('token')}`
            return api(originalRequest)
          })
        }

        isRefreshing = true
        originalRequest._retry = true

        try {
          const { data } = await axios.post(api.defaults.baseURL + '/auth/refresh', null, {
            headers: { Authorization: `Bearer ${refreshToken}` },
          })
          localStorage.setItem('token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token || '')
          pendingRequests.forEach(p => p.resolve())
          pendingRequests = []
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          return api(originalRequest)
        } catch {
          pendingRequests.forEach(p => p.reject(err))
          pendingRequests = []
          _forceLogout()
        } finally {
          isRefreshing = false
        }
      } else {
        _forceLogout()
      }
    } else if (err.response?.status === 429) {
      ElMessage.warning('请求过于频繁，请稍后再试')
    } else if (err.response?.status !== 401) {
      ElMessage.error(msg)
    }
    return Promise.reject(err)
  },
)

export default api
