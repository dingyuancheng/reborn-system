import request from './request'

export function getStats() {
  return request.get('/api/admin/stats')
}

export function uploadIcon(file: File) {
  const form = new FormData()
  form.append('file', file)
  return request.post('/api/admin/upload/icon', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}