import api from './index'

export const login = (data) => api.post('/auth/login', data)
export const refreshToken = () => {
  const refresh = localStorage.getItem('refresh_token')
  return api.post('/auth/refresh', null, {
    headers: { Authorization: `Bearer ${refresh}` },
  })
}
export const logout = () => api.post('/auth/logout')
