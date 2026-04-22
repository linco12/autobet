import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const matchesApi = {
  list: (params) => api.get('/matches/', { params }),
  today: () => api.get('/matches/today'),
  get: (id) => api.get(`/matches/${id}`),
}

export const predictionsApi = {
  top: (params) => api.get('/predictions/top', { params }),
  stats: () => api.get('/predictions/stats'),
  refresh: () => api.post('/predictions/refresh'),
  get: (matchId) => api.get(`/predictions/${matchId}`),
}

export const recipientsApi = {
  list: () => api.get('/recipients/'),
  add: (data) => api.post('/recipients/', data),
  update: (id, data) => api.patch(`/recipients/${id}`, data),
  remove: (id) => api.delete(`/recipients/${id}`),
  test: (id) => api.post(`/recipients/${id}/test`),
  logs: () => api.get('/recipients/logs'),
}

export const adminApi = {
  health: () => api.get('/health'),
  sendNow: () => api.post('/admin/send-whatsapp-now'),
}

export default api
