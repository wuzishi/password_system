import api from './index'

export const getAuditLogs = (params) => api.get('/audit', { params })
