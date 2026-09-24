<template>
  <div class="page">
    <el-card>
      <div class="toolbar">
        <div class="title">会话管理 - 在线 {{ sessions.length }} 人</div>
        <div class="filters">
          <el-select v-model="filterUser" placeholder="按用户筛选" clearable style="width: 180px" @change="loadData">
            <el-option v-for="u in uniqueUsers" :key="u.id" :label="`${u.username} (${u.nickname || '-'})`" :value="u.username" />
          </el-select>
          <el-button :icon="Refresh" circle @click="loadData" />
        </div>
      </div>

      <el-table :data="filteredSessions" v-loading="loading" stripe>
        <el-table-column prop="username" label="账号" width="140" />
        <el-table-column prop="nickname" label="昵称" width="140">
          <template #default="{ row }">{{ row.nickname || '-' }}</template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="device" label="设备" min-width="200" show-overflow-tooltip />
        <el-table-column prop="user_agent" label="浏览器" min-width="200" show-overflow-tooltip />
        <el-table-column prop="login_time" label="登录时间" width="180">
          <template #default="{ row }">{{ formatTime(row.login_time) }}</template>
        </el-table-column>
        <el-table-column prop="last_active" label="最后活跃" width="180">
          <template #default="{ row }">{{ formatTime(row.last_active) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewKey(row)">查看KEY</el-button>
            <el-popconfirm title="确定踢下线？会通知用户" @confirm="kick(row)">
              <template #reference>
                <el-button link type="danger" size="small">踢下线</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="rawDialogVisible" title="Redis Key 详情" width="600px">
      <div v-if="rawData" class="raw-content">
        <div class="raw-row">
          <span class="raw-label">Key：</span>
          <el-input :model-value="rawData.key" readonly size="small" />
        </div>
        <div class="raw-row">
          <span class="raw-label">TTL：</span>
          <span>{{ rawData.ttl }} 秒（约 {{ Math.ceil(rawData.ttl / 3600) }} 小时）</span>
        </div>
        <div class="raw-row" style="margin-top: 12px">
          <div class="raw-label">Value（JSON）：</div>
          <pre class="raw-json">{{ JSON.stringify(rawData.payload, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { listSessions, kickSession, getSessionRaw } from '@/api/session'

const loading = ref(false)
const filterUser = ref('')
const sessions = ref<any[]>([])
let timer: number | null = null

const rawDialogVisible = ref(false)
const rawData = ref<any>(null)

const uniqueUsers = computed(() => {
  const map = new Map()
  sessions.value.forEach((s) => {
    if (!map.has(s.username)) map.set(s.username, { id: s.user_id, username: s.username, nickname: s.nickname })
  })
  return Array.from(map.values())
})

const filteredSessions = computed(() => {
  if (!filterUser.value) return sessions.value
  return sessions.value.filter((s) => s.username === filterUser.value)
})

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    sessions.value = (await listSessions()) as any[]
  } finally {
    loading.value = false
  }
}

async function kick(row: any) {
  const reason = prompt('请输入踢下线原因（用户会看到）：', '管理员强制下线') || '管理员强制下线'
  await kickSession(row.session_id, reason)
  ElMessage.success('已踢下线')
  await loadData()
}

async function viewKey(row: any) {
  try {
    rawData.value = await getSessionRaw(row.session_id)
    rawDialogVisible.value = true
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '查询失败')
  }
}

onMounted(() => {
  loadData()
  timer = window.setInterval(loadData, 15000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.title { font-size: 16px; font-weight: 600; }
.filters { display: flex; gap: 12px; }
.raw-content { padding: 0 8px; }
.raw-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.raw-label {
  font-weight: 600;
  color: #374151;
  min-width: 120px;
  flex-shrink: 0;
}
.raw-json {
  background: #1f2937;
  color: #e5e7eb;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  margin: 0;
}
</style>