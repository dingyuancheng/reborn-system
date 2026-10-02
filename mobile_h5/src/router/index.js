import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory('/h5/'),
  routes: [
    {
      path: '/go-game',
      name: 'GoGame',
      component: () => import('@/views/go-game/index.vue')
    }
  ]
})

export default router