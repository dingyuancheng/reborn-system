<template>
  <div class="page">
    <el-card>
      <div class="toolbar">
        <div class="filters">
          <el-select v-model="filterCat" placeholder="按分类筛选" clearable style="width: 160px" @change="loadData">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-select v-model="filterStatus" placeholder="按状态筛选" clearable style="width: 140px" @change="loadData">
            <el-option label="正常" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </div>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增菜单</el-button>
      </div>

      <el-table :data="menus" v-loading="loading" stripe>
        <el-table-column prop="icon" label="图标" width="80">
          <template #default="{ row }">{{ row.icon || '-' }}</template>
        </el-table-column>
        <el-table-column prop="name" label="菜单名" width="140" />
        <el-table-column prop="url" label="路径/URL" min-width="200" show-overflow-tooltip />
        <el-table-column label="分类" width="120">
          <template #default="{ row }">{{ getCatName(row.category_id) }}</template>
        </el-table-column>
        <el-table-column label="外链" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.external" type="warning" size="small">外链</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort" label="排序" width="70" />
        <el-table-column label="可见" width="80">
          <template #default="{ row }">
            <el-switch :model-value="row.visible === 1" @change="(v: boolean) => quickUpdate(row, { visible: v ? 1 : 0 })" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-switch :model-value="row.status === 1" @change="(v: boolean) => quickUpdate(row, { status: v ? 1 : 0 })" />
          </template>
        </el-table-column>
        <el-table-column label="有效期" width="200">
          <template #default="{ row }">
            <span v-if="row.start_time || row.end_time">
              {{ row.start_time ? row.start_time.substring(0, 10) : '无' }} → {{ row.end_time ? row.end_time.substring(0, 10) : '永' }}
            </span>
            <span v-else class="gray">永久</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDialog(row)">编辑</el-button>
            <el-popconfirm title="软删除：标记为不可用" @confirm="handleDelete(row, false)">
              <template #reference>
                <el-button link type="warning" size="small">软删</el-button>
              </template>
            </el-popconfirm>
            <el-popconfirm title="永久删除不可恢复" confirm-button-type="danger" @confirm="handleDelete(row, true)">
              <template #reference>
                <el-button link type="danger" size="small">硬删</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑菜单' : '新增菜单'" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="form.category_id" style="width: 100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="图标">
          <div style="display: flex; gap: 8px; align-items: center">
            <el-input v-model="form.icon" placeholder="emoji" style="width: 140px" />
            <el-popover placement="bottom" width="280" trigger="click">
              <div class="emoji-grid">
                <span v-for="e in emojiList" :key="e" class="emoji-item" @click="form.icon = e">{{ e }}</span>
              </div>
              <template #reference>
                <el-button :icon="Picture" circle />
              </template>
            </el-popover>
            <el-upload
              action=""
              :show-file-list="false"
              :before-upload="handleUploadIcon"
              accept="image/*"
            >
              <el-button :icon="Upload" circle />
            </el-upload>
          </div>
        </el-form-item>
        <el-form-item label="菜单名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="URL/路径" prop="url">
          <el-input v-model="form.url" placeholder="/chore/cook 或 https://..." />
        </el-form-item>
        <el-form-item label="外链">
          <el-switch v-model="form.external" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch :model-value="form.status === 1" @change="(v: boolean) => (form.status = v ? 1 : 0)" />
        </el-form-item>
        <el-form-item label="可见">
          <el-switch :model-value="form.visible === 1" @change="(v: boolean) => (form.visible = v ? 1 : 0)" />
        </el-form-item>
        <el-form-item label="有效期">
          <el-date-picker
            v-model="form.valid_range"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            style="width: 100%"
          />
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
import { Plus, Picture, Upload } from '@element-plus/icons-vue'
import { listMenus, createMenu, updateMenu, updateMenuStatus, deleteMenu } from '@/api/menu'
import { listCategories } from '@/api/category'
import { uploadIcon } from '@/api/system'

const emojiList = ['🧹', '💰', '🏠', '❤️', '🔧', '🍳', '📊', '📷', '📅', '🤖', '⚙️', '🎮', '📚', '🏋️', '🎵', '🎬', '📱', '🚗', '🛒', '🎁']

const loading = ref(false)
const saving = ref(false)
const filterCat = ref('')
const filterStatus = ref<number | undefined>(undefined)
const menus = ref<any[]>([])
const categories = ref<any[]>([])

const dialogVisible = ref(false)
const editing = ref<any>(null)
const formRef = ref<FormInstance>()
const form = ref<any>({
  category_id: '', icon: '', name: '', url: '', external: 0, sort: 0,
  status: 1, visible: 1, valid_range: null,
})
const rules: FormRules = {
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  name: [{ required: true, message: '请输入菜单名', trigger: 'blur' }],
  url: [{ required: true, message: '请输入 URL/路径', trigger: 'blur' }],
}

function getCatName(id: string) {
  return categories.value.find((c) => c.id === id)?.name || '-'
}

async function loadData() {
  loading.value = true
  try {
    const [menuRes, catRes]: any[] = await Promise.all([
      listMenus(filterCat.value || undefined, filterStatus.value),
      listCategories(),
    ])
    menus.value = menuRes || []
    categories.value = catRes || []
  } finally {
    loading.value = false
  }
}

async function quickUpdate(row: any, patch: any) {
  try {
    await updateMenuStatus(row.id, patch)
    Object.assign(row, patch)
  } catch {
    loadData()
  }
}

function openDialog(row?: any) {
  editing.value = row || null
  if (row) {
    form.value = {
      category_id: row.category_id, icon: row.icon || '', name: row.name,
      url: row.url, external: row.external, sort: row.sort,
      status: row.status, visible: row.visible,
      valid_range: row.start_time && row.end_time
        ? [new Date(row.start_time), new Date(row.end_time)]
        : null,
    }
  } else {
    form.value = {
      category_id: filterCat.value || categories.value[0]?.id || '',
      icon: '', name: '', url: '', external: 0, sort: (menus.value.length + 1) * 10,
      status: 1, visible: 1, valid_range: null,
    }
  }
  dialogVisible.value = true
}

async function handleUploadIcon(file: File) {
  try {
    const res: any = await uploadIcon(file)
    form.value.icon = res.icon_url || res.url || res.filename
    ElMessage.success('上传成功')
  } catch {
    // ignore
  }
  return false
}

async function handleSave() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const payload: any = {
        category_id: form.value.category_id,
        icon: form.value.icon || null,
        name: form.value.name,
        url: form.value.url,
        external: form.value.external,
        sort: form.value.sort,
        status: form.value.status,
        visible: form.value.visible,
        start_time: form.value.valid_range ? form.value.valid_range[0].toISOString() : null,
        end_time: form.value.valid_range ? form.value.valid_range[1].toISOString() : null,
      }
      if (editing.value) {
        await updateMenu(editing.value.id, payload)
        ElMessage.success('已更新')
      } else {
        await createMenu(payload)
        ElMessage.success('已创建')
      }
      dialogVisible.value = false
      await loadData()
    } finally {
      saving.value = false
    }
  })
}

async function handleDelete(row: any, hard: boolean) {
  await deleteMenu(row.id, hard)
  ElMessage.success(hard ? '已永久删除' : '已软删除')
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
.filters { display: flex; gap: 12px; }
.gray { color: #9ca3af; }
.emoji-grid {
  display: grid; grid-template-columns: repeat(8, 1fr); gap: 4px;
}
.emoji-item { cursor: pointer; font-size: 20px; text-align: center; padding: 4px; border-radius: 4px; }
.emoji-item:hover { background: #f3f4f6; }
</style>