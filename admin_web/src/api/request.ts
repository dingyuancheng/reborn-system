import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { useUserStore } from '@/stores/user'

const instance: AxiosInstance = axios.create({
  timeout: 15000,
})

instance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const userStore = useUserStore()
    if (userStore.sessionId && config.headers) {
      config.headers['X-Session-Id'] = userStore.sessionId
    }
    return config
  },
  (error) => Promise.reject(error),
)

instance.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail || error.message || '请求失败'

    if (status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      ElMessage.error('登录已过期，请重新登录')
      router.push('/login')
      return Promise.reject(error)
    }

    if (status === 403 && typeof detail === 'string' && (detail.includes('强制下线') || detail.includes('重新登录') || detail.includes('失效') || detail.includes('封禁') || detail.includes('禁用'))) {
      ElMessage.warning(detail)
      const userStore = useUserStore()
      userStore.logout()
      router.push('/login')
      return Promise.reject(error)
    }

    if (status === 403) {
      ElMessage.error(detail)
      return Promise.reject(error)
    }

    ElMessage.error(detail)
    return Promise.reject(error)
  },
)

export default instance