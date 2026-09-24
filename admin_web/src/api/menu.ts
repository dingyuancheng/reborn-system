import request from './request'

export interface MenuItem {
  id: string
  category_id: string
  name: string
  url: string
  icon: string | null
  sort: number
  external: number
  visible: number
  status: number
  start_time: string | null
  end_time: string | null
}

export function listMenus(category_id?: string, status_filter?: number) {
  const params: any = {}
  if (category_id) params.category_id = category_id
  if (status_filter !== undefined && status_filter !== null) params.status_filter = status_filter
  return request.get('/api/admin/menus', { params })
}

export function createMenu(data: any) {
  return request.post('/api/admin/menus', data)
}

export function updateMenu(id: string, data: any) {
  return request.put(`/api/admin/menus/${id}`, data)
}

export function updateMenuStatus(id: string, data: { status?: number; visible?: number }) {
  return request.put(`/api/admin/menus/${id}/status`, data)
}

export function deleteMenu(id: string, hard = false) {
  return request.delete(`/api/admin/menus/${id}`, { params: { hard } })
}