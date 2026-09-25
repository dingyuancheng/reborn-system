import axios from 'axios'
import { showToast, showDialog } from 'vant'
import storage, { KEY } from '@/utils/storage'
import { getActiveDomain } from '@/config/domain'
import { store } from '@/store'

const isInternalUrl = (url) => {
  if (!url) return false
  return !url.startsWith('http://') && !url.startsWith('https://')
}

const getEffectiveBaseURL = () => {
  if (window.Capacitor) {
    const domain = getActiveDomain()
    if (domain) return domain
    return 'http://localhost:8000'
  }
  return ''
}

const request = axios.create({
  timeout: 15000,
})

request.interceptors.request.use((config) => {
  const sessionId = store.sessionId || storage.get(KEY.sessionId)
  if (sessionId) {
    config.headers['X-Session-Id'] = sessionId
  }

  if (isInternalUrl(config.url)) {
    config.baseURL = getEffectiveBaseURL()
  }

  return config
})

request.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    const msg = error.message || ''
    const code = error.code || ''
    const fullUrl = (error.config?.baseURL || '') + (error.config?.url || '')

    console.error('[Request Error]', {
      url: fullUrl,
      status,
      detail,
      msg,
      code,
    })

    if (error.code === 'ERR_NETWORK' || !error.response) {
      await showDialog({
        title: '网络错误',
        message: `请求地址：\n${fullUrl}\n\n错误码：${code}\n错误信息：${msg}\n\nCapacitor: ${!!window.Capacitor}\n域名: ${getActiveDomain() || '(未设置)'}`,
        confirmButtonText: '知道了',
        showCancelButton: false,
      })
    } else if (status === 401 && !error.config?.url?.includes('/login')) {
      store.sessionId = ''
      store.user = null
      storage.remove(KEY.sessionId)
      storage.remove(KEY.userInfo)
      showToast('登录已过期，请重新登录')
      window.location.hash = '#/login'
    } else if (status === 403 && typeof detail === 'string' && (detail.includes('强制下线') || detail.includes('重新登录') || detail.includes('封禁') || detail.includes('失效') || detail.includes('禁用'))) {
      store.sessionId = ''
      store.user = null
      storage.remove(KEY.sessionId)
      storage.remove(KEY.userInfo)
      showToast(detail)
      window.location.hash = '#/login'
    } else if (detail) {
      showToast(detail)
    } else {
      showToast(`请求失败 (${status || '无响应'})`)
    }

    return Promise.reject(error)
  }
)

export default request