<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #dbeafe; color: #2563eb"><el-icon :size="28"><User /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_users || 0 }}</div>
            <div class="stat-label">总用户数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #dcfce7; color: #16a34a"><el-icon :size="28"><View /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.online_users || 0 }}</div>
            <div class="stat-label">在线用户</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #fef3c7; color: #d97706"><el-icon :size="28"><House /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_families || 0 }}</div>
            <div class="stat-label">家庭数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #fce7f3; color: #db2777"><el-icon :size="28"><Menu /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_menus || 0 }}</div>
            <div class="stat-label">菜单数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card class="stat-card small" shadow="hover">
          <div class="stat-icon" style="background: #e0e7ff; color: #4f46e5"><el-icon :size="24"><TrendCharts /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.today_clicks || 0 }}</div>
            <div class="stat-label">今日点击</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card small" shadow="hover">
          <div class="stat-icon" style="background: #fce7f3; color: #be185d"><el-icon :size="24"><Calendar /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.today_logins || 0 }}</div>
            <div class="stat-label">今日登录</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🔥 常用菜单 TOP6</span>
            </div>
          </template>
          <div v-if="stats.top_menus?.length" class="top-menus">
            <div v-for="(menu, idx) in stats.top_menus" :key="idx" class="top-menu-item">
              <span class="rank" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span>
              <div class="menu-icon-block" :style="getMenuIconStyle(menu)">
                <span v-for="(char, cIdx) in getMenuIconChars(menu)" :key="cIdx" class="menu-icon-char">{{ char }}</span>
              </div>
              <span class="name">{{ menu.name }}</span>
              <span class="count">{{ menu.click_count }} 次</span>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近登录</span>
              <el-button size="small" text @click="loadData">刷新</el-button>
            </div>
          </template>
          <el-table :data="stats.recent_users || []" size="small" empty-text="暂无数据">
            <el-table-column prop="nickname" label="昵称" width="120" />
            <el-table-column prop="username" label="账号" width="100" />
            <el-table-column prop="last_login_time" label="登录时间" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { getStats } from '@/api/system'
import { User, View, House, Menu, TrendCharts, Calendar } from '@element-plus/icons-vue'

const stats = ref<any>({})
let timer: number | null = null

const ICON_BGS = ['#0ea5e9', '#f59e0b', '#10b981', '#8b5cf6', '#f43f5e', '#06b6d4', '#f97316', '#6366f1', '#14b8a6', '#d946ef']

function hashStr(s: string) {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h + s.charCodeAt(i)) | 0
  }
  return h
}

function getAutoBgColor(s: string) {
  if (!s) return '#0ea5e9'
  const idx = Math.abs(hashStr(s)) % ICON_BGS.length
  return ICON_BGS[idx]
}

function getMenuIconChars(menu: any) {
  const text = menu.icon_text || menu.name || ''
  return text.split('')
}

function getMenuIconStyle(menu: any) {
  let bg = '#0ea5e9'
  if (menu.icon_color && (menu.icon_color.startsWith('#') || menu.icon_color.startsWith('rgb'))) {
    bg = menu.icon_color
  } else if (menu.icon_color && menu.icon_color.startsWith('linear-gradient')) {
    bg = menu.icon_color
  } else {
    bg = getAutoBgColor(menu.icon_text || menu.name || '')
  }
  const color = menu.icon_text_color || '#ffffff'
  return { background: bg, color }
}

async function loadData() {
  try {
    const res: any = await getStats()
    stats.value = res
  } catch (e) {
    // ignore
  }
}

onMounted(() => {
  loadData()
  timer = window.setInterval(loadData, 30000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.stat-row {
  margin-bottom: 20px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 90px;
}
.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px 16px 40px;
  width: 100%;
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stat-icon.small {
  width: 48px;
  height: 48px;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}
.stat-label {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
.top-menus {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.top-menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background: #f9fafb;
}
.top-menu-item:hover {
  background: #f3f4f6;
}
.rank {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  background: #e5e7eb;
  color: #6b7280;
}
.rank-1 { background: #fef3c7; color: #d97706; }
.rank-2 { background: #e5e7eb; color: #4b5563; }
.rank-3 { background: #fed7aa; color: #c2410c; }
.menu-icon-block {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 1px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
  flex-shrink: 0;
  overflow: hidden;
  padding: 2px;
}
.menu-icon-char {
  display: flex;
  align-items: center;
  justify-content: center;
}
.name {
  flex: 1;
  font-size: 14px;
  color: #1f2937;
}
.count {
  font-size: 13px;
  color: #6b7280;
}
</style>