import request from './request'

export function listRedisKeys(pattern = 'reborn-*') {
  return request.get('/api/admin/redis/keys', { params: { pattern } })
}

export function getRedisInfo() {
  return request.get('/api/admin/redis/info')
}