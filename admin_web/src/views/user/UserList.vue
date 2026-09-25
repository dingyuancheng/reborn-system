<template>
  <div class="page">
    <el-card>
      <div class="toolbar">
        <div class="filters">
          <el-select v-model="filterFamily" placeholder="按家庭筛选" clearable style="width: 160px">
            <el-option v-for="f in families" :key="f.id" :label="f.name" :value="f.id" />
          </el-select>
          <el-input v-model="keyword" placeholder="搜索用户名/昵称" clearable style="width: 200px" @keyup.enter="loadData">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="filterDeleted" placeholder="用户状态" style="width: 110px">
            <el-option label="全部" :value="null" />
            <el-option label="有效" :value="false" />
            <el-option label="失效" :value="true" />
          </el-select>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增用户</el-button>
      </div>

      <el-table :data="filteredList" v-loading="loading" stripe>
        <el-table-column prop="username" label="账号" width="120" />
        <el-table-column prop="nickname" label="昵称" width="120">
          <template #default="{ row }">{{ row.nickname || '-' }}</template>
        </el-table-column>
        <el-table-column label="性别" width="60">
          <template #default="{ row }">{{ row.gender === 1 ? '男' : row.gender === 0 ? '女' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="family_name" label="所属家庭" width="140">
          <template #default="{ row }">{{ getFamilyName(row.family_id) || '-' }}</template>
        </el-table-column>
        <el-table-column label="角色" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.admin_flag" type="danger" size="small">Admin</el-tag>
            <el-tag v-else type="info" size="small">普通</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.deleted" type="info" size="small">失效</el-tag>
            <el-tag v-else-if="row.ban_flag" type="danger" size="small">已封禁</el-tag>
            <el-tag v-else-if="row.status !== 1" type="warning" size="small">已禁用</el-tag>
            <el-tag v-else type="success" size="small">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_time" label="最后登录" width="180">
          <template #default="{ row }">{{ row.last_login_time ? formatTime(row.last_login_time) : '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <template v-if="row.deleted">
              <el-popconfirm title="确定恢复该用户？" @confirm="handleRestore(row.id)">
                <template #reference>
                  <el-button link type="success" size="small">恢复</el-button>
                </template>
              </el-popconfirm>
            </template>
            <template v-else>
              <el-button link type="primary" size="small" @click="openDialog(row)">编辑</el-button>
              <el-button link type="primary" size="small" @click="openResetPwd(row)">重置密码</el-button>
              <el-button link v-if="row.ban_flag" type="success" size="small" @click="toggleBan(row, false)">解封</el-button>
              <el-button link v-else type="warning" size="small" @click="toggleBan(row, true)">封禁</el-button>
              <el-popconfirm title="确定删除该用户？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑用户' : '新增用户'" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!editing" />
        </el-form-item>
        <el-form-item label="密码" v-if="!editing" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio :value="1">男</el-radio>
            <el-radio :value="0">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="家庭">
          <el-select v-model="form.family_id" clearable style="width: 100%">
            <el-option v-for="f in families" :key="f.id" :label="f.name" :value="f.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="管理员">
          <el-switch v-model="form.admin_flag" />
        </el-form-item>
        <el-form-item label="禁用">
          <el-switch v-model="form._disabled" @change="(v: boolean) => (form.status = v ? 0 : 1)" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resetPwdVisible" title="重置密码" width="400px" destroy-on-close>
      <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-width="80px">
        <el-form-item label="用户名">
          <el-input :model-value="resetForm.username" disabled />
        </el-form-item>
        <el-form-item label="新密码" prop="password">
          <el-input v-model="resetForm.password" type="password" show-password placeholder="至少 6 位" @input="onPwdInput" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="resetForm.confirmPassword" type="password" show-password placeholder="再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleResetPwd">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { listUsers, createUser, updateUser, deleteUser, restoreUser, resetPassword, banUser } from '@/api/user'
import { listFamilies } from '@/api/family'

const loading = ref(false)
const saving = ref(false)
const keyword = ref('')
const filterFamily = ref('')
const filterDeleted = ref<boolean | null>(false)
const users = ref<any[]>([])
const families = ref<any[]>([])

const dialogVisible = ref(false)
const editing = ref<any>(null)
const formRef = ref<FormInstance>()
const form = ref<any>({
  username: '', password: '', nickname: '', gender: 1,
  family_id: null, admin_flag: false, status: 1, _disabled: false,
})
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
}

const resetPwdVisible = ref(false)
const resetFormRef = ref<FormInstance>()
const resetForm = ref({ userId: '', username: '', password: '', confirmPassword: '' })
const resetRules: FormRules = {
  password: [
    { required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value && value !== resetForm.value.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const filteredList = computed(() => {
  let list = users.value
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    list = list.filter((u) =>
      u.username.toLowerCase().includes(kw) || (u.nickname || '').toLowerCase().includes(kw),
    )
  }
  return list
})

function getFamilyName(fid: string | null | undefined) {
  if (!fid) return '-'
  return families.value.find((f) => f.id === fid)?.name
}

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function resetFilters() {
  keyword.value = ''
  filterFamily.value = ''
  filterDeleted.value = false
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const [userRes, famRes]: any[] = await Promise.all([
      listUsers(filterFamily.value || undefined, filterDeleted.value),
      listFamilies(),
    ])
    users.value = (userRes || []).map((u: any) => ({
      ...u,
      family_name: famRes.find((f: any) => f.id === u.family_id)?.name,
    }))
    families.value = famRes || []
  } finally {
    loading.value = false
  }
}

function openDialog(row?: any) {
  editing.value = row || null
  if (row) {
    form.value = {
      username: row.username, nickname: row.nickname, gender: row.gender,
      family_id: row.family_id, admin_flag: row.admin_flag,
      status: row.status, _disabled: row.status !== 1,
    }
  } else {
    form.value = {
      username: '', password: '', nickname: '', gender: 1,
      family_id: null, admin_flag: false, status: 1, _disabled: false,
    }
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const payload: any = { ...form.value }
      delete payload._disabled
      if (editing.value) {
        await updateUser(editing.value.id, payload)
        ElMessage.success('已更新')
      } else {
        await createUser(payload)
        ElMessage.success('已创建')
      }
      dialogVisible.value = false
      await loadData()
    } finally {
      saving.value = false
    }
  })
}

async function handleDelete(id: string) {
  await deleteUser(id)
  ElMessage.success('已删除')
  await loadData()
}

async function handleRestore(id: string) {
  await restoreUser(id)
  ElMessage.success('已恢复')
  await loadData()
}

function openResetPwd(row: any) {
  resetForm.value = { userId: row.id, username: row.username, password: '', confirmPassword: '' }
  resetPwdVisible.value = true
}

function onPwdInput() {
  resetFormRef.value?.validateField('confirmPassword')
}

async function handleResetPwd() {
  if (!resetFormRef.value) return
  await resetFormRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      await resetPassword(resetForm.value.userId, resetForm.value.password)
      ElMessage.success('密码已重置')
      resetPwdVisible.value = false
    } finally {
      saving.value = false
    }
  })
}

async function toggleBan(row: any, ban: boolean) {
  const reason = ban ? prompt('请输入封禁原因（可选）：') : null
  if (reason === null && ban) return
  await banUser(row.id, { ban_flag: ban, ban_reason: reason || null })
  ElMessage.success(ban ? '已封禁' : '已解封')
  await loadData()
}

onMounted(loadData)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.filters {
  display: flex;
  gap: 12px;
}
</style>