import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', component: () => import('@/views/login/LoginPage.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    children: [
      { path: 'dashboard', component: () => import('@/views/dashboard/Dashboard.vue'), meta: { title: '仪表盘' } },
      { path: 'users', component: () => import('@/views/user/UserList.vue'), meta: { title: '用户管理' } },
      { path: 'families', component: () => import('@/views/family/FamilyList.vue'), meta: { title: '家庭管理' } },
      { path: 'categories', component: () => import('@/views/category/CategoryList.vue'), meta: { title: '菜单分类' } },
      { path: 'menus', component: () => import('@/views/menu/MenuList.vue'), meta: { title: '菜单管理' } },
      { path: 'permissions', component: () => import('@/views/permission/PermissionAssign.vue'), meta: { title: '权限分配' } },
      { path: 'sessions', component: () => import('@/views/session/SessionList.vue'), meta: { title: '会话管理' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  if (to.meta.public) {
    next()
    return
  }
  if (!userStore.sessionId) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }
  if (!userStore.userInfo) {
    userStore.fetchUserInfo().then(() => {
      if (userStore.userInfo && !userStore.userInfo.admin_flag) {
        userStore.logout()
        next('/login')
      } else {
        next()
      }
    }).catch(() => {
      userStore.logout()
      next('/login')
    })
    return
  }
  next()
})

export default router