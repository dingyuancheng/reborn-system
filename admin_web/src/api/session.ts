import request from './request'

export function listSessions() {
  return request.get('/api/admin/sessions')
}

export function kickSession(sessionId: string, reason = '管理员强制下线') {
  return request.delete(`/api/admin/sessions/${sessionId}`, { params: { reason } })
}

export function getSessionRaw(sessionId: string) {
  return request.get(`/api/admin/sessions/${sessionId}/raw`)
}