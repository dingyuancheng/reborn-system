import request from './request'

export interface PermissionMenu {
  id: string
  category_id: string
  name: string
  url: string
  icon: string | null
  external: number
}

export function getUserPermissions(userId: string) {
  return request.get(`/api/admin/permissions/${userId}`)
}

export function setUserPermissions(userId: string, menu_ids: string[]) {
  return request.put(`/api/admin/permissions/${userId}`, { menu_ids })
}

export function listAllMenusSimple() {
  return request.get('/api/admin/permissions/all-menus/simple')
}

export function batchAssignPermissions(data: {
  user_ids: string[]
  menu_ids: string[]
  mode: 'replace' | 'add' | 'remove'
}) {
  return request.put('/api/admin/permissions/batch-assign', data)
}