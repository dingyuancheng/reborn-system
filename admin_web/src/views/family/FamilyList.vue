<template>
  <div class="page">
    <el-card>
      <div class="toolbar">
        <div class="title">家庭管理</div>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增家庭</el-button>
      </div>

      <el-table :data="families" v-loading="loading" stripe>
        <el-table-column prop="name" label="家庭名称" width="180" />
        <el-table-column prop="address" label="家庭地址" show-overflow-tooltip>
          <template #default="{ row }">{{ row.address || '-' }}</template>
        </el-table-column>
        <el-table-column prop="description" label="备注" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column prop="member_count" label="成员数" width="80" />
        <el-table-column prop="create_time" label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDialog(row)">编辑</el-button>
            <el-popconfirm title="确定删除？如果还有成员则删除会被拒绝" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑家庭' : '新增家庭'" width="460px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="家庭名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="家庭地址">
          <el-input v-model="form.address" maxlength="255" show-word-limit />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { listFamilies, createFamily, updateFamily, deleteFamily } from '@/api/family'

const loading = ref(false)
const saving = ref(false)
const families = ref<any[]>([])

const dialogVisible = ref(false)
const editing = ref<any>(null)
const formRef = ref<FormInstance>()
const form = ref({ name: '', address: '', description: '' })
const rules: FormRules = {
  name: [{ required: true, message: '请输入家庭名称', trigger: 'blur' }],
}

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    families.value = (await listFamilies()) as any[]
  } finally {
    loading.value = false
  }
}

function openDialog(row?: any) {
  editing.value = row || null
  form.value = row ? { name: row.name, address: row.address || '', description: row.description || '' } : { name: '', address: '', description: '' }
  dialogVisible.value = true
}

async function handleSave() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (editing.value) {
        await updateFamily(editing.value.id, form.value)
        ElMessage.success('已更新')
      } else {
        await createFamily(form.value)
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
  await deleteFamily(id)
  ElMessage.success('已删除')
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
.title {
  font-size: 16px;
  font-weight: 600;
}
</style>