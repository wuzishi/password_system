import api from './index'

export const createApproval = (data) => api.post('/approvals', data)
export const getApprovals = (params) => api.get('/approvals', { params })
export const getPendingCount = () => api.get('/approvals/pending-count')
export const approveRequest = (id) => api.put(`/approvals/${id}/approve`)
export const rejectRequest = (id, data) => api.put(`/approvals/${id}/reject`, data)
export const checkAccess = (passwordId) => api.get(`/approvals/check-access/${passwordId}`)
