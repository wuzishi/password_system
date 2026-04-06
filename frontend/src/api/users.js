import api from './index'

export const getUsers = () => api.get('/users')
export const createUser = (data) => api.post('/users', data)
export const updateUser = (id, data) => api.put(`/users/${id}`, data)
export const deleteUser = (id) => api.delete(`/users/${id}`)
export const getMe = () => api.get('/users/me')
export const changePassword = (data) => api.put('/users/me/password', data)
export const getAllUsers = () => api.get('/users/all')
