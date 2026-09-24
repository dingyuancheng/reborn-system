import request from './request'

export interface UserItem {
  id: string
  username: string
  nickname: string | null
  avatar: string | null
  admin_flag: boolean
  status: number
  ban_flag: boolean
  ban_reason?: string | null
  ban_time?: string | null
  last_login_time?: string | null
  family_id?: string | null
  family_name?: string | null
}

export function listUsers(family_id?: string) {
  const params: any = {}
  if (family_id) params.family_id = family_id
  return request.get('/api/admin/users', { params })
}

export function getUser(id: string) {
  return request.get(`/api/admin/users/${id}`)
}

export function createUser(data: any) {
  return request.post('/api/admin/users', data)
}

export function updateUser(id: string, data: any) {
  return request.put(`/api/admin/users/${id}`, data)
}

export function deleteUser(id: string) {
  return request.delete(`/api/admin/users/${id}`)
}

export function resetPassword(id: string, new_password: string) {
  return request.post(`/api/admin/users/${id}/reset-password`, { new_password })
}

export function banUser(id: string, data: { ban_flag: boolean; ban_reason?: string; ban_time?: string | null }) {
  return request.put(`/api/admin/users/${id}/ban`, data)
}