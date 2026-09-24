import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/api/request'

interface UserInfo {
  id: string
  username: string
  nickname: string | null
  admin_flag: boolean
  family_id: string | null
  avatar: string | null
}

const SESSION_KEY = 'reborn_admin_session'

export const useUserStore = defineStore('user', () => {
  const sessionId = ref<string>(localStorage.getItem(SESSION_KEY) || '')
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!sessionId.value && !!userInfo.value)

  async function login(username: string, password: string) {
    const res: any = await request.post('/api/auth/login', { username, password })
    sessionId.value = res.session_id
    userInfo.value = res.user
    localStorage.setItem(SESSION_KEY, res.session_id)
    if (!res.user.admin_flag) {
      logout()
      throw new Error('非管理员账号，禁止登录后台')
    }
    return res.user
  }

  async function fetchUserInfo() {
    const res: any = await request.get('/api/auth/me')
    userInfo.value = res
    return res
  }

  function logout() {
    sessionId.value = ''
    userInfo.value = null
    localStorage.removeItem(SESSION_KEY)
  }

  return { sessionId, userInfo, isLoggedIn, login, fetchUserInfo, logout }
})