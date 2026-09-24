<template>
  <div class="page">
    <el-card>
      <div class="toolbar">
        <div class="title">菜单分类</div>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增分类</el-button>
      </div>

      <el-alert v-if="dragging" title="拖拽中 - 松开鼠标完成排序" type="info" show-icon :closable="false" style="margin-bottom: 12px" />

      <el-table :data="categories" v-loading="loading" stripe>
        <el-table-column width="60" label="拖拽">
          <template #default="{ row, $index }">
            <span class="drag-handle" :class="{ dragging: dragIndex === $index }" @mousedown="startDrag($index, $event)">⠿</span>
          </template>
        </el-table-column>
        <el-table-column prop="icon" label="图标" width="80">
          <template #default="{ row }">{{ row.icon || '-' }}</template>
        </el-table-column>
        <el-table-column prop="name" label="分类名" width="200" />
        <el-table-column prop="sort" label="排序" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch :model-value="row.status === 1" @change="(v: boolean) => toggleStatus(row, v)" />
          </template>
        </el-table-column>
        <el-table-column prop="menu_count" label="菜单数" width="100" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDialog(row)">编辑</el-button>
            <el-popconfirm title="确定删除？如果有菜单则会被拒绝" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑分类' : '新增分类'" width="420px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="图标">
          <div style="display: flex; gap: 8px; align-items: center">
            <el-input v-model="form.icon" placeholder="emoji 或图标名" style="width: 140px" />
            <el-popover placement="bottom" width="280" trigger="click">
              <div class="emoji-grid">
                <span v-for="e in emojiList" :key="e" class="emoji-item" @click="form.icon = e">{{ e }}</span>
              </div>
              <template #reference>
                <el-button :icon="Picture" circle />
              </template>
            </el-popover>
          </div>
        </el-form-item>
        <el-form-item label="分类名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch :model-value="form.status === 1" @change="(v: boolean) => (form.status = v ? 1 : 0)" />
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
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Picture } from '@element-plus/icons-vue'
import { listCategories, createCategory, updateCategory, deleteCategory } from '@/api/category'

const emojiList = ['🧹', '💰', '🏠', '❤️', '🔧', '🍳', '📊', '📷', '📅', '🤖', '⚙️', '🎮', '📚', '🏋️', '🎵', '🎬', '📱', '🚗', '🛒', '🎁']

const loading = ref(false)
const saving = ref(false)
const categories = ref<any[]>([])

const dialogVisible = ref(false)
const editing = ref<any>(null)
const formRef = ref<FormInstance>()
const form = ref({ name: '', icon: '', sort: 0, status: 1 })
const rules: FormRules = {
  name: [{ required: true, message: '请输入分类名', trigger: 'blur' }],
}

const dragging = ref(false)
const dragIndex = ref(-1)

async function loadData() {
  loading.value = true
  try {
    categories.value = (await listCategories()) as any[]
  } finally {
    loading.value = false
  }
}

function startDrag(idx: number, e: MouseEvent) {
  e.preventDefault()
  dragIndex.value = idx
  dragging.value = true
  const startY = e.clientY

  function onMove(ev: MouseEvent) {
    const diff = ev.clientY - startY
    if (Math.abs(diff) > 20) {
      const direction = diff > 0 ? 1 : -1
      const newIdx = dragIndex.value + direction
      if (newIdx >= 0 && newIdx < categories.value.length) {
        const moved = categories.value.splice(dragIndex.value, 1)[0]
        categories.value.splice(newIdx, 0, moved)
        dragIndex.value = newIdx
      }
    }
  }

  async function onUp() {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
    dragging.value = false
    dragIndex.value = -1
    const updates = categories.value.map((c, i) =>
      updateCategory(c.id, { sort: i + 1 }),
    )
    try {
      await Promise.all(updates)
      ElMessage.success('排序已更新')
    } catch {
      loadData()
    }
  }

  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

async function toggleStatus(row: any, v: boolean) {
  await updateCategory(row.id, { status: v ? 1 : 0 })
  row.status = v ? 1 : 0
}

function openDialog(row?: any) {
  editing.value = row || null
  form.value = row
    ? { name: row.name, icon: row.icon || '', sort: row.sort, status: row.status }
    : { name: '', icon: '', sort: (categories.value.length + 1) * 10, status: 1 }
  dialogVisible.value = true
}

async function handleSave() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (editing.value) {
        await updateCategory(editing.value.id, form.value)
        ElMessage.success('已更新')
      } else {
        await createCategory(form.value)
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
  await deleteCategory(id)
  ElMessage.success('已删除')
  await loadData()
}

onMounted(loadData)
onBeforeUnmount(() => {})
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.title { font-size: 16px; font-weight: 600; }
.drag-handle {
  cursor: grab;
  font-size: 18px;
  color: #9ca3af;
  user-select: none;
}
.drag-handle.dragging { color: #2563eb; cursor: grabbing; }
.emoji-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 4px;
}
.emoji-item {
  cursor: pointer;
  font-size: 20px;
  text-align: center;
  padding: 4px;
  border-radius: 4px;
}
.emoji-item:hover { background: #f3f4f6; }
</style>