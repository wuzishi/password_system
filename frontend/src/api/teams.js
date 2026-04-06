import api from './index'

export const getTeams = () => api.get('/teams')
export const getTeam = (id) => api.get(`/teams/${id}`)
export const createTeam = (data) => api.post('/teams', data)
export const updateTeam = (id, data) => api.put(`/teams/${id}`, data)
export const deleteTeam = (id) => api.delete(`/teams/${id}`)
export const addMember = (teamId, userId) => api.post(`/teams/${teamId}/members`, { user_id: userId })
export const removeMember = (teamId, userId) => api.delete(`/teams/${teamId}/members/${userId}`)
