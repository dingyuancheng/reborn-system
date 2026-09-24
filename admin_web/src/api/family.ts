import request from './request'

export function listFamilies() {
  return request.get('/api/admin/families')
}

export function createFamily(data: { name: string; description?: string }) {
  return request.post('/api/admin/families', data)
}

export function updateFamily(id: string, data: { name?: string; description?: string }) {
  return request.put(`/api/admin/families/${id}`, data)
}

export function deleteFamily(id: string) {
  return request.delete(`/api/admin/families/${id}`)
}