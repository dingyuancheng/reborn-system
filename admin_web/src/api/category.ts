import request from './request'

export interface CategoryItem {
  id: string
  name: string
  icon: string | null
  sort: number
  status: number
  menu_count: number
}

export function listCategories() {
  return request.get('/api/admin/categories')
}

export function createCategory(data: { name: string; icon?: string; sort?: number; status?: number }) {
  return request.post('/api/admin/categories', data)
}

export function updateCategory(id: string, data: any) {
  return request.put(`/api/admin/categories/${id}`, data)
}

export function deleteCategory(id: string) {
  return request.delete(`/api/admin/categories/${id}`)
}