<template>
  <div class="page permission-page">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>选择用户</span>
              <el-input v-model="keyword" placeholder="搜索用户名" clearable size="small" style="width: 140px" :prefix-icon="Search" />
            </div>
          </template>
          <el-table :data="filteredUsers" v-loading="loading" highlight-current-row height="500" @current-change="onUserSelect">
            <el-table-column prop="username" label="账号" width="120" />
            <el-table-column prop="nickname" label="昵称">
              <template #default="{ row }">{{ row.nickname || '-' }}</template>
            </el-table-column>
            <el-table-column label="角色" width="70">
              <template #default="{ row }">
                <el-tag v-if="row.admin_flag" type="danger" size="small">A</el-tag>
                <el-tag v-else type="info" size="small">U</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card v-if="selectedUser">
          <template #header>
            <div class="card-header">
              <span>权限配置 - {{ selectedUser.username }} ({{ selectedUser.nickname || '-' }})</span>
              <div>
                <el-button size="small" :icon="Plus" @click="batchOpen">批量分配</el-button>
                <el-button size="small" @click="loadPerms(selectedUser.id)">刷新</el-button>
              </div>
            </div>
          </template>
          <div class="perm-header">
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button value="tree">树形视图</el-radio-button>
              <el-radio-button value="list">平铺视图</el-radio-button>
            </el-radio-group>
            <div class="perm-actions">
              <el-checkbox v-model="checkAll" :indeterminate="indeterminate" @change="handleCheckAll">全选</el-checkbox>
              <el-button type="primary" :loading="saving" size="small" @click="savePerms">保存</el-button>
            </div>
          </div>

          <div v-if="viewMode === 'tree'" class="perm-tree">
            <el-tree
              ref="treeRef"
              :data="treeData"
              :props="{ label: 'label', children: 'children' }"
              show-checkbox
              node-key="id"
              :default-checked-keys="checkedKeys"
              @check="onTreeCheck"
            />
          </div>
          <div v-else class="perm-list">
            <div v-for="cat in flatByCategory" :key="cat.id" class="perm-group">
              <div class="cat-header">{{ cat.name }}</div>
              <el-checkbox-group v-model="currentMenuIds">
                <el-checkbox v-for="m in cat.menus" :key="m.id" :value="m.id">
                  {{ m.icon }} {{ m.name }} <span class="url">({{ m.url }})</span>
                </el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
        </el-card>
        <el-card v-else class="empty-card">
          <el-empty description="请从左侧选择一个用户" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="batchVisible" title="批量分配权限" width="600px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="选择用户">
          <el-select v-model="batchUsers" multiple collapse-tags collapse-tags-tooltip style="width: 100%" placeholder="选择多个用户">
            <el-option v-for="u in users" :key="u.id" :label="u.username" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作模式">
          <el-radio-group v-model="batchMode">
            <el-radio value="replace">替换（覆盖所有权限）</el-radio>
            <el-radio value="add">追加权限</el-radio>
            <el-radio value="remove">移除权限</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <el-tree
        :data="treeData"
        :props="{ label: 'label', children: 'children' }"
        show-checkbox
        node-key="id"
        :default-checked-keys="batchMenuIds"
        ref="batchTreeRef"
      />
      <template #footer>
        <el-button @click="batchVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleBatchSave">执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, type TreeInstance } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { listUsers } from '@/api/user'
import { listCategories } from '@/api/category'
import { listMenus } from '@/api/menu'
import { getUserPermissions, setUserPermissions, batchAssignPermissions } from '@/api/permission'

const loading = ref(false)
const saving = ref(false)
const keyword = ref('')
const users = ref<any[]>([])
const categories = ref<any[]>([])
const menus = ref<any[]>([])
const selectedUser = ref<any>(null)
const currentMenuIds = ref<string[]>([])
const checkedKeys = ref<string[]>([])
const treeRef = ref<TreeInstance>()
const batchTreeRef = ref<TreeInstance>()

const viewMode = ref<'tree' | 'list'>('list')

const filteredUsers = computed(() => {
  if (!keyword.value) return users.value
  const kw = keyword.value.toLowerCase()
  return users.value.filter((u) =>
    u.username.toLowerCase().includes(kw) || (u.nickname || '').toLowerCase().includes(kw),
  )
})

const treeData = computed(() => {
  return categories.value.map((c) => ({
    id: c.id,
    label: c.name,
    isCategory: true,
    children: menus.value
      .filter((m) => m.category_id === c.id)
      .map((m) => ({ id: m.id, label: `${m.icon || ''} ${m.name}`.trim() })),
  }))
})

const flatByCategory = computed(() => {
  return categories.value.map((c) => ({
    id: c.id,
    name: c.name,
    menus: menus.value.filter((m) => m.category_id === c.id),
  }))
})

const checkAll = computed({
  get: () => currentMenuIds.value.length === menus.value.length && menus.value.length > 0,
  set: () => {},
})
const indeterminate = computed(() => {
  return currentMenuIds.value.length > 0 && currentMenuIds.value.length < menus.value.length
})

function handleCheckAll(val: boolean) {
  currentMenuIds.value = val ? menus.value.map((m) => m.id) : []
}

function onTreeCheck() {
  nextTick(() => {
    if (treeRef.value) {
      const keys: string[] = []
      treeRef.value.getCheckedNodes().forEach((node: any) => {
        if (!node.isCategory) keys.push(node.id)
      })
      currentMenuIds.value = keys
    }
  })
}

async function loadData() {
  loading.value = true
  try {
    const [uRes, cRes, mRes]: any[] = await Promise.all([
      listUsers(),
      listCategories(),
      listMenus(),
    ])
    users.value = uRes || []
    categories.value = cRes || []
    menus.value = mRes || []
  } finally {
    loading.value = false
  }
}

function onUserSelect(row: any) {
  selectedUser.value = row
  if (row) loadPerms(row.id)
}

async function loadPerms(userId: string) {
  loading.value = true
  try {
    const res: any = await getUserPermissions(userId)
    const menuIds: string[] = (res || []).map((m: any) => m.id)
    currentMenuIds.value = menuIds
    checkedKeys.value = menuIds
    await nextTick()
    if (treeRef.value) {
      treeRef.value.setCheckedKeys([...menuIds, ...categories.value.map((c) => c.id)])
    }
  } finally {
    loading.value = false
  }
}

async function savePerms() {
  if (!selectedUser.value) return
  saving.value = true
  try {
    await setUserPermissions(selectedUser.value.id, currentMenuIds.value)
    ElMessage.success('已保存')
  } finally {
    saving.value = false
  }
}

const batchVisible = ref(false)
const batchUsers = ref<string[]>([])
const batchMode = ref<'replace' | 'add' | 'remove'>('replace')
const batchMenuIds = ref<string[]>([])

function batchOpen() {
  batchUsers.value = []
  batchMode.value = 'replace'
  batchMenuIds.value = [...currentMenuIds.value]
  batchVisible.value = true
  nextTick(() => {
    if (batchTreeRef.value) {
      batchTreeRef.value.setCheckedKeys([...batchMenuIds.value, ...categories.value.map((c) => c.id)])
    }
  })
}

function getBatchMenuIds() {
  const checked: string[] = []
  const nodes: any[] = batchTreeRef.value?.getCheckedNodes() || []
  nodes.forEach((n) => {
    if (!n.isCategory) checked.push(n.id)
  })
  return checked
}

async function handleBatchSave() {
  if (!batchUsers.value.length) {
    ElMessage.warning('请选择用户')
    return
  }
  const menuIds = getBatchMenuIds()
  saving.value = true
  try {
    await batchAssignPermissions({
      user_ids: batchUsers.value,
      menu_ids: menuIds,
      mode: batchMode.value,
    })
    ElMessage.success('批量分配成功')
    batchVisible.value = false
  } finally {
    saving.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.perm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}
.perm-actions { display: flex; gap: 12px; align-items: center; }
.perm-tree { padding: 12px; background: #f9fafb; border-radius: 8px; max-height: 500px; overflow-y: auto; }
.perm-list { display: flex; flex-direction: column; gap: 16px; max-height: 500px; overflow-y: auto; padding: 8px; }
.perm-group { background: #f9fafb; border-radius: 8px; padding: 12px; }
.cat-header { font-weight: 600; margin-bottom: 8px; color: #374151; }
.url { color: #9ca3af; font-size: 12px; }
.empty-card { display: flex; justify-content: center; align-items: center; min-height: 400px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
</style>