import request from './request'

export function listSessions(): Promise<any[]> {
  return request.get('/api/admin/sessions') as unknown as Promise<any[]>
}

export function kickSession(sessionId: string, reason = '管理员强制下线') {
  return request.delete(`/api/admin/sessions/${sessionId}`, { params: { reason } })
}

export function getSessionRaw(sessionId: string) {
  return request.get(`/api/admin/sessions/${sessionId}/raw`)
}