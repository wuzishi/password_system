import api from './index'

export const getMyPermissions = () => api.get('/permissions/my')
export const getAllPermissions = () => api.get('/permissions')
export const updatePermissions = (data) => api.put('/permissions', data)
