import api from './index'

export const getPasswords = (params) => api.get('/passwords', { params })
export const getExpiringPasswords = () => api.get('/passwords/expiring')
export const createPassword = (data) => api.post('/passwords', data)
export const updatePassword = (id, data) => api.put(`/passwords/${id}`, data)
export const deletePassword = (id) => api.delete(`/passwords/${id}`)
export const decryptPassword = (id, data = {}) => api.post(`/passwords/${id}/decrypt`, data)
export const sharePassword = (id, data) => api.post(`/passwords/${id}/share`, data)
export const getShares = (id) => api.get(`/passwords/${id}/shares`)
export const revokeShare = (passwordId, shareId) => api.delete(`/passwords/${passwordId}/share/${shareId}`)
export const verifyServerPassword = (id) => api.post(`/passwords/${id}/verify-server`)
