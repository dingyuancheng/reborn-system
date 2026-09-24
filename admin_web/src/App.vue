<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

onMounted(async () => {
  if (userStore.sessionId) {
    try {
      await userStore.fetchUserInfo()
    } catch {
      userStore.logout()
      router.push('/login')
    }
  }
})
</script>