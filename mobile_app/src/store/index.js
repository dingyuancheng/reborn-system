import storage, { KEY } from '@/utils/storage'
import { reactive } from 'vue'
import request from '@/utils/request'

const HEARTBEAT_INTERVAL = 15000

let heartbeatTimer = null

export const store = reactive({
  user: null,
  sessionId: '',
  menus: [],
  categories: [],
  frequentMenus: [],
  serverConfig: null,
})

function startHeartbeat() {
  stopHeartbeat()
  heartbeatTimer = setInterval(async () => {
    if (!store.sessionId) {
      stopHeartbeat()
      return
    }
    try {
      await request.get('/api/auth/session-info')
    } catch {
      stopHeartbeat()
    }
  }, HEARTBEAT_INTERVAL)
}

function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

export function initStore() {
  store.sessionId = storage.get(KEY.sessionId, '') || ''
  const userInfo = storage.get(KEY.userInfo)
  if (userInfo) {
    store.user = userInfo
  }
  if (store.sessionId) {
    startHeartbeat()
  }
}

export function setAuth(sessionId, user) {
  store.sessionId = sessionId
  store.user = user
  storage.set(KEY.sessionId, sessionId)
  storage.set(KEY.userInfo, user)
  startHeartbeat()
}

export function clearAuth() {
  stopHeartbeat()
  store.sessionId = ''
  store.user = null
  storage.remove(KEY.sessionId)
  storage.remove(KEY.userInfo)
}

export function setMenuData(data) {
  store.menus = data.menus || []
  store.categories = data.categories || []
  store.frequentMenus = data.frequent_menus || []
}

export function isLoggedIn() {
  return !!store.sessionId
}