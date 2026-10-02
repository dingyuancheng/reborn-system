<template>
  <div class="page">
    <el-card>
      <div class="toolbar">
        <div class="filters">
          <el-input v-model="keyword" placeholder="搜索菜单名称/路径" clearable style="width: 240px" @keyup.enter="loadData">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="filterCat" placeholder="按分类筛选" clearable style="width: 160px" @change="loadData">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-select v-model="filterStatus" placeholder="按状态筛选" clearable style="width: 140px" @change="loadData">
            <el-option label="正常" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增菜单</el-button>
      </div>

      <el-table :data="filteredMenus" v-loading="loading" stripe>
        <el-table-column prop="icon_text" label="图标" width="80" align="center">
          <template #default="{ row }">
            <div class="icon-block" :style="getIconBlockStyle(row)">
              <span v-for="(char, idx) in getPreviewChars(row.icon_text || (row.name ? row.name.charAt(0) : ''))" :key="idx" class="icon-char">{{ char }}</span>
            </div>
          </template>
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
        <el-form-item label="图标文字">
          <div style="display: flex; gap: 12px; align-items: center">
            <el-input v-model="form.icon_text" placeholder="图标块内显示的文字，如:五子棋 邮 支" style="width: 200px" maxlength="6" clearable />
            <div class="icon-block" :style="iconBlockStyle">
              <span v-for="(char, idx) in getPreviewChars(form.icon_text || (form.name ? form.name.charAt(0) : ''))" :key="idx" class="icon-char">{{ char }}</span>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="背景色">
          <div style="display: flex; gap: 12px; align-items: center">
            <el-radio-group v-model="bgMode" size="small" @change="onBgModeChange">
              <el-radio-button value="solid">纯色</el-radio-button>
              <el-radio-button value="gradient">渐变</el-radio-button>
            </el-radio-group>
            <template v-if="bgMode === 'solid'">
              <el-color-picker v-model="bgColor" :predefine="colorPresets" show-alpha />
            </template>
            <template v-else>
              <span style="font-size: 12px; color: #909399">起始</span>
              <el-color-picker v-model="gradientFrom" :predefine="colorPresets" />
              <span style="font-size: 12px; color: #909399">结束</span>
              <el-color-picker v-model="gradientTo" :predefine="colorPresets" />
            </template>
          </div>
        </el-form-item>

        <el-form-item label="文字色">
          <el-color-picker v-model="textColor" :predefine="colorPresets" />
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
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete, Search } from '@element-plus/icons-vue'
import { listMenus, createMenu, updateMenu, updateMenuStatus, deleteMenu } from '@/api/menu'
import { listCategories } from '@/api/category'

const loading = ref(false)
const saving = ref(false)
const keyword = ref('')
const filterCat = ref('')
const filterStatus = ref<number | undefined>(undefined)
const menus = ref<any[]>([])
const categories = ref<any[]>([])

const filteredMenus = computed(() => {
  let result = menus.value
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    result = result.filter((m) =>
      (m.name || '').toLowerCase().includes(kw) ||
      (m.url || '').toLowerCase().includes(kw),
    )
  }
  if (filterCat.value) {
    result = result.filter((m) => m.category_id === filterCat.value)
  }
  if (filterStatus.value !== undefined) {
    result = result.filter((m) => m.status === filterStatus.value)
  }
  return result
})

function resetFilters() {
  keyword.value = ''
  filterCat.value = ''
  filterStatus.value = undefined
  loadData()
}

const dialogVisible = ref(false)
const editing = ref<any>(null)
const formRef = ref<FormInstance>()
const form = ref<any>({
  category_id: '', icon: '', icon_text: '', icon_color: '', icon_text_color: '', name: '', url: '', external: 0, sort: 0,
  status: 1, visible: 1, valid_range: null,
})
const rules: FormRules = {
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  name: [{ required: true, message: '请输入菜单名', trigger: 'blur' }],
  url: [{ required: true, message: '请输入 URL/路径', trigger: 'blur' }],
}

// ===== 自定义颜色选择 =====
const bgMode = ref<'solid' | 'gradient'>('solid')
const bgColor = ref('')
const gradientFrom = ref('')
const gradientTo = ref('')
const textColor = ref('')

const colorPresets = [
  '#0ea5e9', '#f59e0b', '#10b981', '#8b5cf6', '#f43f5e',
  '#06b6d4', '#f97316', '#6366f1', '#14b8a6', '#d946ef',
  '#ffffff', '#1e293b',
]

// 自动分配背景色（旧逻辑保留作兜底）
const ICON_BGS = ['#0ea5e9', '#f59e0b', '#10b981', '#8b5cf6', '#f43f5e', '#06b6d4', '#f97316', '#6366f1', '#14b8a6', '#d946ef']
function getAutoBgColor(s: string) {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h + s.charCodeAt(i)) | 0
  }
  return ICON_BGS[Math.abs(h) % ICON_BGS.length]
}

// 计算最终背景色 CSS 值
const iconBlockBg = computed(() => {
  if (bgMode.value === 'gradient' && gradientFrom.value && gradientTo.value) {
    return `linear-gradient(135deg, ${gradientFrom.value}, ${gradientTo.value})`
  }
  if (bgColor.value) return bgColor.value
  // 没选色时自动分配
  const text = form.value.icon_text || form.value.name || ''
  return text ? getAutoBgColor(text) : '#0ea5e9'
})

// 计算最终文字色
const iconBlockTextColor = computed(() => {
  return textColor.value || '#ffffff'
})

// 预览块 style
const iconBlockStyle = computed(() => ({
  background: iconBlockBg.value,
  color: iconBlockTextColor.value,
}))

// 监听颜色变化，同步到 form.icon_color / icon_text_color
watch([bgMode, bgColor, gradientFrom, gradientTo], () => {
  form.value.icon_color = iconBlockBg.value
}, { deep: true })
watch(textColor, (v) => {
  form.value.icon_text_color = v || '#ffffff'
})

function onBgModeChange() {
  if (bgMode.value === 'solid' && !bgColor.value) {
    bgColor.value = getAutoBgColor(form.value.icon_text || form.value.name || '')
  }
}

function getCatName(id: string) {
  return categories.value.find((c) => c.id === id)?.name || '-'
}

function getPreviewChars(text: string) {
  return text.split('')
}

function getIconBlockStyle(row: any) {
  const bg = row.icon_color || getAutoBgColor(row.name || '')
  const color = row.icon_text_color || '#ffffff'
  return { background: bg, color }
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

function parseIconColor(val?: string) {
  if (!val) return { mode: 'solid' as const, bgColor: '', gradientFrom: '', gradientTo: '', textColor: '' }
  if (val.startsWith('linear-gradient')) {
    const m = val.match(/linear-gradient\(135deg,\s*(#[0-9a-fA-F]{3,8})\s*,\s*(#[0-9a-fA-F]{3,8})\s*\)/)
    return m
      ? { mode: 'gradient' as const, bgColor: '', gradientFrom: m[1], gradientTo: m[2], textColor: '' }
      : { mode: 'solid' as const, bgColor: val, gradientFrom: '', gradientTo: '', textColor: '' }
  }
  return { mode: 'solid' as const, bgColor: val, gradientFrom: '', gradientTo: '', textColor: '' }
}

function openDialog(row?: any) {
  editing.value = row || null
  if (row) {
    form.value = {
      category_id: row.category_id, icon: row.icon || '', icon_text: row.icon_text || '',
      icon_color: row.icon_color || '', icon_text_color: row.icon_text_color || '',
      name: row.name, url: row.url, external: row.external, sort: row.sort,
      status: row.status, visible: row.visible,
      valid_range: row.start_time && row.end_time
        ? [new Date(row.start_time), new Date(row.end_time)]
        : null,
    }
    const parsed = parseIconColor(row.icon_color)
    bgMode.value = parsed.mode
    bgColor.value = parsed.bgColor
    gradientFrom.value = parsed.gradientFrom
    gradientTo.value = parsed.gradientTo
    textColor.value = row.icon_text_color || ''
  } else {
    form.value = {
      category_id: filterCat.value || categories.value[0]?.id || '',
      icon: '', icon_text: '', icon_color: '', icon_text_color: '', name: '', url: '', external: 0, sort: (menus.value.length + 1) * 10,
      status: 1, visible: 1, valid_range: null,
    }
    bgMode.value = 'solid'
    bgColor.value = ''
    gradientFrom.value = ''
    gradientTo.value = ''
    textColor.value = ''
  }
  dialogVisible.value = true
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
        icon_text: form.value.icon_text || null,
        icon_color: form.value.icon_color || null,
        icon_text_color: form.value.icon_text_color || null,
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

.icon-block {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 1px;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
  flex-shrink: 0;
  overflow: hidden;
  padding: 2px;
}

.icon-char {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>