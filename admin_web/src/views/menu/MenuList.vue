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
        <el-table-column prop="icon" label="图标" width="90">
          <template #default="{ row }">
            <div v-if="row.icon" class="icon-preview" :class="row.icon_color || getIconBgClass(row.name || row.icon)">
              <el-icon v-if="allIconNames.includes(row.icon)" :size="20">
                <component :is="row.icon" />
              </el-icon>
              <img v-else-if="/\.(png|jpg|jpeg|svg|webp|gif)$/i.test(row.icon)" :src="row.icon" style="width:20px;height:20px;object-fit:contain" />
              <span v-else style="font-size:18px">{{ row.icon }}</span>
            </div>
            <el-icon v-else style="color:#c0c4cc"><CircleCloseFilled /></el-icon>
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
        <el-form-item label="图标">
          <div style="display: flex; gap: 8px; align-items: center">
            <el-input v-model="form.icon" placeholder="输入图标名(如HomeFilled)" style="width: 180px" clearable />
            <el-popover v-model:visible="iconPopVisible" placement="bottom" width="340" trigger="click">
              <div class="icon-picker">
                <el-input v-model="iconSearch" placeholder="搜索图标(如user)" clearable size="small" style="margin-bottom: 8px" />
                <div class="icon-grid">
                  <div 
                    v-for="icon in filteredIcons" 
                    :key="icon" 
                    class="icon-item" 
                    :class="{ active: form.icon === icon }"
                    @click="selectIcon(icon)"
                    :title="icon"
                  >
                    <component :is="icon" :size="18" />
                  </div>
                </div>
                <div class="icon-tip">共{{ allIconNames.length }}个Element Plus图标</div>
              </div>
              <template #reference>
                <el-button :icon="Grid" circle title="从200+图标中选择" />
              </template>
            </el-popover>
            <el-tooltip content="清空图标" placement="top">
              <el-button :icon="Delete" circle @click="form.icon = ''" />
            </el-tooltip>
          </div>
        </el-form-item>
        <el-form-item label="配色">
          <div class="color-picker">
            <div 
              class="color-swatch auto" 
              :class="{ active: !form.icon_color }"
              @click="form.icon_color = ''"
              title="自动分配"
            >
              <el-icon :size="14"><Refresh /></el-icon>
            </div>
            <div
              v-for="c in ICON_BGS"
              :key="c"
              class="color-swatch"
              :class="[c, { active: form.icon_color === c }]"
              @click="form.icon_color = c"
              :title="c.replace('bg-','')"
            />
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Grid, Delete, Refresh } from '@element-plus/icons-vue'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { listMenus, createMenu, updateMenu, updateMenuStatus, deleteMenu } from '@/api/menu'
import { listCategories } from '@/api/category'

const allIconNames = Object.keys(ElementPlusIconsVue)

const ICON_ALIAS: Record<string, string> = {
  AddLocation: '添加位置 定位',
  Aim: '瞄准 目标 中心',
  AlarmClock: '闹钟 时钟 时间',
  Apple: '苹果 水果',
  ArrowDown: '向下箭头 下拉',
  ArrowDownBold: '向下箭头 下拉 粗体',
  ArrowLeft: '向左箭头 返回',
  ArrowLeftBold: '向左箭头 粗体',
  ArrowRight: '向右箭头',
  ArrowRightBold: '向右箭头 粗体',
  ArrowUp: '向上箭头 上拉',
  ArrowUpBold: '向上箭头 粗体',
  Avatar: '头像 用户',
  Back: '返回 后退',
  Baseball: '棒球 运动',
  Basketball: '篮球 运动',
  Bell: '铃铛 通知',
  BellFilled: '铃铛 通知 实心',
  Bicycle: '自行车 车辆',
  Bottom: '底部 下方 下',
  BottomLeft: '左下 左下角',
  BottomRight: '右下 右下角',
  Bowl: '碗 餐具',
  Box: '盒子 包裹 箱子',
  Briefcase: '公文包 工作 职业',
  Brush: '刷子 画笔 美术',
  BrushFilled: '刷子 画笔 实心',
  Burger: '汉堡 快餐',
  Calendar: '日历 日程 日期',
  Camera: '相机 拍照',
  CameraFilled: '相机 拍照 实心',
  CaretBottom: '下箭头 下拉',
  CaretLeft: '左箭头',
  CaretRight: '右箭头',
  CaretTop: '上箭头',
  Cellphone: '手机 电话',
  ChatDotRound: '消息 聊天 对话 圆形',
  ChatDotSquare: '消息 聊天 方形',
  ChatLineRound: '聊天 对话 圆形',
  ChatLineSquare: '聊天 对话 方形',
  ChatRound: '聊天 对话 圆形',
  ChatSquare: '聊天 对话 方形',
  Check: '勾选 完成 对勾',
  Checked: '勾选 已完成',
  Cherry: '樱桃 水果',
  Chicken: '鸡肉 食物',
  ChromeFilled: '浏览器 谷歌',
  CircleCheck: '圆形勾选 成功',
  CircleCheckFilled: '圆形勾选 成功 实心',
  CircleClose: '圆形关闭 失败',
  CircleCloseFilled: '圆形关闭 失败 实心',
  CirclePlus: '圆形加号 添加',
  CirclePlusFilled: '圆形加号 添加 实心',
  Clock: '时钟 时间',
  Close: '关闭 取消',
  CloseBold: '关闭 粗体',
  Cloudy: '多云 天气',
  Coffee: '咖啡 饮品',
  CoffeeCup: '咖啡杯 饮品',
  Coin: '金币 钱 财务',
  ColdDrink: '冷饮 饮品',
  Collection: '集合 收藏 收集',
  CollectionTag: '标签 分类 收藏',
  Comment: '评论 留言',
  Compass: '指南针 导航 方向',
  Connection: '连接 网络 链接',
  Coordinate: '坐标 定位 地图',
  CopyDocument: '复制文档 拷贝文件',
  Cpu: '处理器 CPU 服务器 数据',
  CreditCard: '信用卡 银行卡 支付',
  Crop: '裁剪 图片编辑',
  DArrowLeft: '双左箭头 翻页',
  DArrowRight: '双右箭头 翻页',
  DCaret: '下拉箭头',
  DataAnalysis: '数据分析 图表 统计',
  DataBoard: '数据看板 仪表盘',
  DataLine: '数据折线图 趋势',
  Delete: '删除',
  DeleteFilled: '删除 实心',
  DeleteLocation: '删除位置 定位',
  Dessert: '甜点 甜品',
  Discount: '折扣 优惠 打折',
  Dish: '菜 菜品 餐具',
  DishDot: '菜品 点心',
  Document: '文档 文件',
  DocumentAdd: '添加文档 新建文件',
  DocumentChecked: '已确认文档',
  DocumentCopy: '复制文档',
  DocumentDelete: '删除文档',
  DocumentRemove: '移除文档',
  Download: '下载',
  Drizzling: '小雨 天气',
  Edit: '编辑 修改',
  EditPen: '编辑笔 钢笔 修改',
  Eleme: '饿了么 外卖',
  ElemeFilled: '饿了么 外卖 实心',
  ElementPlus: 'Element Plus 图标',
  Expand: '展开 扩展',
  Failed: '失败',
  Female: '女性 女士',
  Files: '多文件 文档组',
  Film: '电影 视频',
  Filter: '筛选 过滤',
  Finished: '已完成 结束',
  FirstAidKit: '急救箱 医疗 健康',
  Flag: '旗帜 标记 标签',
  Fold: '折叠 收起',
  Folder: '文件夹 目录',
  FolderAdd: '添加文件夹',
  FolderChecked: '已选文件夹',
  FolderDelete: '删除文件夹',
  FolderOpened: '打开的文件夹',
  FolderRemove: '移除文件夹',
  Food: '食物 餐饮',
  Football: '足球 运动',
  ForkSpoon: '刀叉勺 餐具',
  Fries: '薯条 快餐',
  FullScreen: '全屏',
  Goblet: '酒杯 高脚杯',
  GobletFull: '满杯',
  GobletSquare: '方形酒杯',
  GobletSquareFull: '方形满杯',
  GoldMedal: '金牌 冠军',
  Goods: '商品 物品 货物',
  GoodsFilled: '商品 实心',
  Grape: '葡萄 水果',
  Grid: '网格 九宫格 布局',
  Guide: '引导 指南 帮助',
  Handbag: '手提包 包',
  Headset: '耳机 客服',
  Help: '帮助 问号',
  HelpFilled: '帮助 问号 实心',
  Hide: '隐藏 不可见',
  Histogram: '柱状图 图表',
  HomeFilled: '首页 家 房子 实心',
  HotWater: '热水 饮品',
  House: '房子 家 住宅',
  IceCream: '冰淇淋',
  IceCreamRound: '圆形冰淇淋',
  IceCreamSquare: '方形冰淇淋',
  IceDrink: '冰饮',
  IceTea: '冰茶',
  InfoFilled: '信息 提示 实心',
  Iphone: '苹果手机 手机',
  Key: '钥匙 密码',
  KnifeFork: '刀叉 餐具',
  Lightning: '闪电 快充',
  Link: '链接 外链',
  List: '列表 清单',
  Loading: '加载 载入',
  Location: '位置 定位',
  LocationFilled: '位置 定位 实心',
  LocationInformation: '位置信息 定位',
  Lock: '锁定 安全 密码',
  Lollipop: '棒棒糖 糖果',
  MagicStick: '魔法棒 魔术',
  Magnet: '磁铁 磁石',
  Male: '男性 男士',
  Management: '管理 运营',
  MapLocation: '地图定位',
  Medal: '奖牌 勋章 荣誉',
  Memo: '备忘录 笔记',
  Menu: '菜单 列表',
  Message: '消息 聊天',
  MessageBox: '消息框 通知',
  Mic: '麦克风 录音',
  Microphone: '麦克风 录音',
  MilkTea: '奶茶 饮品',
  Minus: '减少 减号',
  Money: '钱 金钱 财务',
  Monitor: '显示器 电脑 屏幕',
  Moon: '月亮 夜间',
  MoonNight: '月夜 夜晚',
  More: '更多',
  MoreFilled: '更多 实心',
  MostlyCloudy: '阴天 多云',
  Mouse: '鼠标 电脑',
  Mug: '马克杯 杯子',
  Mute: '静音 声音关闭',
  MuteNotification: '通知静音',
  NoSmoking: '禁止吸烟',
  Notebook: '笔记本 笔记',
  Notification: '通知 提醒',
  Odometer: '仪表盘 仪表 数据',
  OfficeBuilding: '办公楼 公司 大厦',
  Open: '打开',
  Operation: '操作 工具',
  Opportunity: '机会 时机',
  Orange: '橙子 水果',
  Paperclip: '回形针 附件',
  PartlyCloudy: '局部多云',
  Pear: '梨 水果',
  Phone: '电话 手机',
  PhoneFilled: '电话 手机 实心',
  Picture: '图片 照片',
  PictureFilled: '图片 照片 实心',
  PictureRounded: '圆角图片',
  PieChart: '饼图',
  Place: '地点 位置',
  Platform: '平台 站点',
  Plus: '添加 新增 加号',
  Pointer: '指针 指示',
  Position: '位置 定位',
  Postcard: '明信片 卡片',
  Pouring: '倒杯 倾倒',
  Present: '礼物 礼品',
  PriceTag: '价格标签',
  Printer: '打印机 打印',
  Promotion: '促销 推广 活动',
  QuartzWatch: '石英表 手表',
  QuestionFilled: '问号 帮助 实心',
  Rank: '排名 排行',
  Reading: '阅读 学习 书本',
  ReadingLamp: '阅读灯 台灯',
  Refresh: '刷新 同步',
  RefreshLeft: '向左刷新',
  RefreshRight: '向右刷新',
  Refrigerator: '冰箱 家电',
  Remove: '移除 去掉',
  RemoveFilled: '移除 实心',
  Right: '右',
  ScaleToOriginal: '缩放 还原',
  School: '学校 学习 教育',
  Scissor: '剪刀 裁剪',
  Search: '搜索 查询 查找',
  Select: '选择',
  Sell: '销售 卖出',
  SemiSelect: '半选 部分选择',
  Service: '服务 客服',
  SetUp: '搭建 建立',
  Setting: '设置 齿轮 系统',
  Share: '分享',
  Ship: '船 轮船 海运',
  Shop: '商店 店铺',
  ShoppingBag: '购物袋 商城',
  ShoppingCart: '购物车 商城',
  ShoppingCartFull: '满的购物车',
  ShoppingTrolley: '购物车 推车',
  Smoking: '吸烟',
  Soccer: '足球 运动',
  SoldOut: '售罄 缺货',
  Sort: '排序',
  SortDown: '降序',
  SortUp: '升序',
  Stamp: '邮票 印章',
  Star: '星星 收藏',
  StarFilled: '星星 收藏 实心',
  Stopwatch: '秒表 计时器',
  SuccessFilled: '成功 对勾 实心',
  Sugar: '糖',
  Suitcase: '行李箱 手提箱',
  SuitcaseLine: '行李箱 线条',
  Sunny: '晴天 太阳 天气',
  Sunrise: '日出',
  Sunset: '日落',
  Switch: '开关 切换',
  SwitchButton: '开关按钮',
  SwitchFilled: '开关 实心',
  TakeawayBox: '外卖盒 打包',
  Ticket: '票 单据',
  Tickets: '多票 单据组',
  Timer: '计时器 计时',
  ToiletPaper: '卫生纸',
  Tools: '工具 扳手 设置',
  Top: '顶部 上方 上',
  TopLeft: '左上 左上角',
  TopRight: '右上 右上角',
  TrendCharts: '趋势图表 数据',
  Trophy: '奖杯 成就 荣誉',
  TrophyBase: '奖杯底座',
  TurnOff: '关闭 关机',
  Umbrella: '雨伞 雨具',
  Unlock: '解锁',
  Upload: '上传',
  UploadFilled: '上传 实心',
  User: '用户 人',
  UserFilled: '用户 人 实心',
  Van: '货车 物流 车辆',
  VideoCamera: '视频 拍摄',
  VideoCameraFilled: '视频 拍摄 实心',
  VideoPause: '视频 暂停',
  VideoPlay: '视频 播放',
  View: '查看 预览',
  Wallet: '钱包 财务',
  WalletFilled: '钱包 财务 实心',
  WarnTriangleFilled: '警告三角 实心',
  Warning: '警告 提醒',
  WarningFilled: '警告 提醒 实心',
  Watch: '手表 时间',
  Watermelon: '西瓜 水果',
  WindPower: '风力 能源',
  ZoomIn: '放大',
  ZoomOut: '缩小',
}

function matchIcon(name: string, kw: string) {
  if (name.toLowerCase().includes(kw)) return true
  const alias = ICON_ALIAS[name]
  if (alias && alias.toLowerCase().includes(kw)) return true
  return false
}

const iconSearch = ref('')
const iconPopVisible = ref(false)
const filteredIcons = computed(() => {
  if (!iconSearch.value.trim()) return allIconNames
  const kw = iconSearch.value.trim().toLowerCase()
  return allIconNames.filter(name => matchIcon(name, kw))
})

function selectIcon(icon: string) {
  form.value.icon = icon
  iconPopVisible.value = false
}

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
  category_id: '', icon: '', icon_color: '', name: '', url: '', external: 0, sort: 0,
  status: 1, visible: 1, valid_range: null,
})
const rules: FormRules = {
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  name: [{ required: true, message: '请输入菜单名', trigger: 'blur' }],
  url: [{ required: true, message: '请输入 URL/路径', trigger: 'blur' }],
}

const ICON_BGS = [
  'bg-sky', 'bg-amber', 'bg-emerald', 'bg-violet',
  'bg-rose', 'bg-cyan', 'bg-orange', 'bg-indigo',
  'bg-teal', 'bg-fuchsia',
]
function getIconBgClass(s: string) {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h + s.charCodeAt(i)) | 0
  }
  return ICON_BGS[Math.abs(h) % ICON_BGS.length]
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
      category_id: row.category_id, icon: row.icon || '', icon_color: row.icon_color || '', name: row.name,
      url: row.url, external: row.external, sort: row.sort,
      status: row.status, visible: row.visible,
      valid_range: row.start_time && row.end_time
        ? [new Date(row.start_time), new Date(row.end_time)]
        : null,
    }
  } else {
    form.value = {
      category_id: filterCat.value || categories.value[0]?.id || '',
      icon: '', icon_color: '', name: '', url: '', external: 0, sort: (menus.value.length + 1) * 10,
      status: 1, visible: 1, valid_range: null,
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
      const payload: any = {
        category_id: form.value.category_id,
        icon: form.value.icon || null,
        icon_color: form.value.icon_color || null,
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

.icon-preview {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff !important;
  --el-icon-color: #fff;
}
.icon-preview :deep(svg) {
  fill: currentColor;
}
.bg-sky     { background: linear-gradient(135deg, #0ea5e9, #38bdf8); }
.bg-amber   { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
.bg-emerald { background: linear-gradient(135deg, #10b981, #34d399); }
.bg-violet  { background: linear-gradient(135deg, #8b5cf6, #a78bfa); }
.bg-rose    { background: linear-gradient(135deg, #f43f5e, #fb7185); }
.bg-cyan    { background: linear-gradient(135deg, #06b6d4, #22d3ee); }
.bg-orange  { background: linear-gradient(135deg, #f97316, #fb923c); }
.bg-indigo  { background: linear-gradient(135deg, #6366f1, #818cf8); }
.bg-teal    { background: linear-gradient(135deg, #14b8a6, #2dd4bf); }
.bg-fuchsia { background: linear-gradient(135deg, #d946ef, #e879f9); }

.color-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.color-swatch {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.color-swatch:hover {
  transform: scale(1.1);
}
.color-swatch.active {
  border-color: #303133;
  box-shadow: 0 0 0 2px #fff inset, 0 0 0 3px #303133;
}
.color-swatch.auto {
  background: #f3f4f6;
  color: #606266;
  border-style: dashed;
}
.color-swatch.auto.active {
  border-color: #303133;
  box-shadow: 0 0 0 2px #fff inset, 0 0 0 3px #303133;
}

.icon-picker { }
.icon-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 4px;
  max-height: 240px;
  overflow-y: auto;
  padding: 4px;
}
.icon-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  color: #606266;
  transition: all 0.2s;
}
.icon-item:hover {
  background: #ecf5ff;
  color: #409eff;
}
.icon-item.active {
  background: #409eff;
  color: #fff;
}
.icon-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}
</style>