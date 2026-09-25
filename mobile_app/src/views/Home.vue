<template>
  <div class="home-page">
    <div class="grid-bg"></div>

    <div class="hero">
      <div class="hero-top">
        <div class="greet">
          <div class="greet-hi">{{ greeting }}，{{ nickname }}</div>
          <div class="greet-sub">
            {{ dateText }}
            <span class="dot-sep"></span>
            {{ familyName }}
          </div>
        </div>
      </div>

      <div class="search-wrap">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          v-model="searchKeyword"
          type="text"
          class="search-input"
          placeholder="搜索功能"
        />
        <button v-if="searchKeyword" class="search-clear" @click="searchKeyword = ''">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>

    <div class="body">
      <div class="panel">
        <div class="tabs-row">
          <button
            v-for="(cat, idx) in categories"
            :key="cat.id"
            type="button"
            class="tab-btn"
            :class="{ active: idx === activeCategory }"
            @click="activeCategory = idx"
          >
            {{ cat.name }}
          </button>
        </div>

        <div
          class="menu-grid"
          @touchstart="onTouchStart"
          @touchmove="onTouchMove"
          @touchend="onTouchEnd"
          @touchcancel="onTouchEnd"
        >
          <div class="swipe-track" :style="swipeTrackStyle">
            <div
              v-for="(panel, pIdx) in swipePanels"
              :key="panel.key"
              class="grid-inner"
              :style="panelStyle(pIdx)"
            >
              <template v-if="panel.mode === 'cat'">
                <div
                  v-for="menu in getMenusByCategory(categories[panel.index]?.id)"
                  :key="menu.id"
                  class="menu-item"
                  @click="!isDragging && openMenu(menu)"
                >
                  <div class="menu-icon-wrap" :class="getIconBgClass(menu)">
                    <component v-if="isSvgIcon(menu.icon)" :is="menu.icon" class="icon-svg" />
                    <img v-else-if="isImageIcon(menu.icon)" :src="menu.icon" class="icon-img" />
                    <span v-else class="icon-emoji">{{ menu.icon || '📦' }}</span>
                    <span v-if="menu.external === 1" class="external-tag">外链</span>
                  </div>
                  <div class="menu-name">{{ menu.name }}</div>
                </div>
                <div v-if="getMenusByCategory(categories[panel.index]?.id).length === 0" class="empty-hint">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <line x1="9" y1="9" x2="15" y2="15"/>
                    <line x1="15" y1="9" x2="9" y2="15"/>
                  </svg>
                  <span>暂无功能</span>
                </div>
              </template>
              <template v-else>
                <div
                  v-for="menu in filteredAllMenus"
                  :key="menu.id"
                  class="menu-item"
                  @click="!isDragging && openMenu(menu)"
                >
                  <div class="menu-icon-wrap" :class="getIconBgClass(menu)">
                    <component v-if="isSvgIcon(menu.icon)" :is="menu.icon" class="icon-svg" />
                    <img v-else-if="isImageIcon(menu.icon)" :src="menu.icon" class="icon-img" />
                    <span v-else class="icon-emoji">{{ menu.icon || '📦' }}</span>
                    <span v-if="menu.external === 1" class="external-tag">外链</span>
                  </div>
                  <div class="menu-name">{{ menu.name }}</div>
                </div>
                <div v-if="filteredAllMenus.length === 0" class="empty-hint">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"/>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  <span>未找到匹配的功能</span>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { store, setMenuData } from '@/store'
import { getMyMenus, recordMenuClick } from '@/api/user'
import { buildMenuUrl } from '@/config/domain'
import storage, { KEY } from '@/utils/storage'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const svgIconSet = new Set(Object.keys(ElementPlusIconsVue))
const isSvgIcon = (icon) => icon && svgIconSet.has(icon)
const isImageIcon = (icon) => icon && /\.(png|jpg|jpeg|svg|webp|gif)$/i.test(icon)

const ICON_BGS = [
  'bg-sky', 'bg-amber', 'bg-emerald', 'bg-violet',
  'bg-rose', 'bg-cyan', 'bg-orange', 'bg-indigo',
  'bg-teal', 'bg-fuchsia',
]

const router = useRouter()
const activeCategory = ref(0)
const searchKeyword = ref('')
const isDragging = ref(false)
const dragOffset = ref(0)
const trackWidth = ref(0)
const animating = ref(false)

const nickname = computed(() => store.user?.nickname || store.user?.username || '用户')
const categories = computed(() => store.categories || [])
const menus = computed(() => store.menus || [])
const familyName = computed(() => store.familyName || 'Reborn 系统')

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const dateText = computed(() => {
  const d = new Date()
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return `${d.getMonth() + 1}月${d.getDate()}日 ${weekdays[d.getDay()]}`
})

const filteredAllMenus = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase()
  if (!kw) return []
  return menus.value.filter((m) => m.name.toLowerCase().includes(kw))
})

const getPanelKey = (catIdx) => {
  if (searchKeyword.value.trim()) return 'search'
  if (!categories.value[catIdx]) return 'empty'
  return 'cat-' + categories.value[catIdx].id
}

const swipePanels = computed(() => {
  if (searchKeyword.value.trim()) {
    return [{ key: 'search', mode: 'search', index: 0, position: 0 }]
  }
  const cats = categories.value
  const cur = activeCategory.value
  const panels = []
  if (cur > 0) panels.push({ key: getPanelKey(cur - 1), mode: 'cat', index: cur - 1, position: -1 })
  panels.push({ key: getPanelKey(cur), mode: 'cat', index: cur, position: 0 })
  if (cur < cats.length - 1) panels.push({ key: getPanelKey(cur + 1), mode: 'cat', index: cur + 1, position: 1 })
  return panels
})

const swipeTrackStyle = computed(() => {
  const w = trackWidth.value || 1
  const curIdx = swipePanels.value.findIndex((p) => p.position === 0)
  const base = -curIdx * w
  const offset = isDragging.value || animating.value ? dragOffset.value : 0
  const transition = animating.value ? 'transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)' : 'none'
  return {
    transform: `translateX(${base + offset}px)`,
    transition,
  }
})

const panelStyle = (pIdx) => {
  const w = trackWidth.value || 0
  return {
    width: w + 'px',
    flex: `0 0 ${w}px`,
  }
}

const updateTrackWidth = () => {
  const el = document.querySelector('.menu-grid')
  if (el) trackWidth.value = el.offsetWidth
}

let touchStartX = 0
let touchStartY = 0
let lockedAxis = null

const onTouchStart = (e) => {
  if (searchKeyword.value.trim()) return
  if (!categories.value.length) return
  if (animating.value) return
  updateTrackWidth()
  touchStartX = e.touches[0].clientX
  touchStartY = e.touches[0].clientY
  dragOffset.value = 0
  isDragging.value = true
  lockedAxis = null
}

const onTouchMove = (e) => {
  if (!isDragging.value) return
  const dx = e.touches[0].clientX - touchStartX
  const dy = e.touches[0].clientY - touchStartY
  if (lockedAxis === null) {
    if (Math.abs(dy) > Math.abs(dx)) {
      isDragging.value = false
      return
    }
    lockedAxis = 'x'
  }
  const w = trackWidth.value
  const curIdx = activeCategory.value
  let offset = dx
  if (curIdx === 0 && dx > 0) offset = dx * 0.3
  if (curIdx === categories.value.length - 1 && dx < 0) offset = dx * 0.3
  dragOffset.value = offset
}

const onTouchEnd = async () => {
  if (!isDragging.value) return
  isDragging.value = false
  const w = trackWidth.value
  const dx = dragOffset.value
  const threshold = w * 0.25
  let targetIdx = activeCategory.value
  if (dx < -threshold && activeCategory.value < categories.value.length - 1) {
    targetIdx = activeCategory.value + 1
  } else if (dx > threshold && activeCategory.value > 0) {
    targetIdx = activeCategory.value - 1
  }
  if (targetIdx !== activeCategory.value) {
    animating.value = true
    dragOffset.value = dx
    await nextTick()
    setTimeout(() => {
      dragOffset.value = -(targetIdx - activeCategory.value) * w
    }, 10)
    setTimeout(() => {
      activeCategory.value = targetIdx
      dragOffset.value = 0
      animating.value = false
    }, 320)
  } else {
    animating.value = true
    await nextTick()
    dragOffset.value = 0
    setTimeout(() => { animating.value = false }, 320)
  }
}

const getIconBgClass = (menu) => {
  if (menu.icon_color && menu.icon_color.startsWith('bg-')) return menu.icon_color
  const idx = Math.abs(hashStr(menu.name)) % ICON_BGS.length
  return ICON_BGS[idx]
}

function hashStr(s) {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h) + s.charCodeAt(i)
    h |= 0
  }
  return h
}

const getMenusByCategory = (catId) => {
  if (!catId) return []
  return menus.value.filter((m) => String(m.category_id) === String(catId))
}

const appendSessionToUrl = (url) => {
  const sid = storage.get(KEY.sessionId) || ''
  if (!sid) return url
  const sep = url.includes('?') ? '&' : '?'
  return `${url}${sep}_sid=${encodeURIComponent(sid)}`
}

const openMenu = async (menu) => {
  try {
    await recordMenuClick(menu.id)
  } catch { /* ignore */ }

  const baseUrl = buildMenuUrl(menu.url, menu.external)
  const fullUrl = menu.external === 0 ? appendSessionToUrl(baseUrl) : baseUrl

  const AppWebView = window.Capacitor?.Plugins?.AppWebView
  const isNative = window.Capacitor?.isNativePlatform?.()

  if (isNative && AppWebView) {
    try {
      await AppWebView.open({ url: fullUrl, title: menu.name || '' })
    } catch (e) {
      console.warn('AppWebView 打开失败，降级为 WebView', e)
      router.push({ name: 'WebView', query: { url: fullUrl, name: menu.name, external: menu.external } })
    }
  } else {
    router.push({ name: 'WebView', query: { url: fullUrl, name: menu.name, external: menu.external } })
  }
}

const loadMenus = async () => {
  try {
    const res = await getMyMenus()
    setMenuData(res)
  } catch (e) {
    console.error('加载菜单失败', e)
  }
}

onMounted(async () => {
  await loadMenus()
  nextTick(() => {
    updateTrackWidth()
    window.addEventListener('resize', updateTrackWidth)
  })
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  padding-bottom: 96px;
  background: #f5f5f4;
  position: relative;
}

.grid-bg {
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, 0.03) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: radial-gradient(ellipse at top, black 20%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse at top, black 20%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.hero {
  position: relative;
  z-index: 2;
  padding: 56px 28px 20px;
}

.hero-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.greet-hi {
  font-size: 24px;
  font-weight: 600;
  letter-spacing: -0.5px;
  color: #1c1c1e;
  line-height: 1.3;
}

.greet-sub {
  font-size: 12px;
  color: #8a8a8e;
  margin-top: 6px;
  display: flex;
  align-items: center;
}

.dot-sep {
  display: inline-block;
  width: 3px;
  height: 3px;
  background: #0ea5e9;
  border-radius: 50%;
  margin: 0 8px;
}

.search-wrap {
  margin-top: 20px;
  display: flex;
  align-items: center;
  height: 46px;
  padding: 0 14px;
  background: #ffffff;
  border: 1px solid #e7e5e4;
  border-radius: 12px;
  gap: 10px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.search-wrap:focus-within {
  border-color: #0ea5e9;
  box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.1);
}

.search-icon {
  width: 15px;
  height: 15px;
  color: #b8b5b0;
  flex-shrink: 0;
}
.search-wrap:focus-within .search-icon {
  color: #0ea5e9;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  font-weight: 500;
  color: #1c1c1e;
  height: 100%;
}
.search-input::placeholder {
  color: #b8b5b0;
  font-weight: 400;
}

.search-clear {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  background: #e7e5e4;
  border-radius: 50%;
  color: #57534e;
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
}
.search-clear svg {
  width: 12px;
  height: 12px;
}

.body {
  position: relative;
  z-index: 2;
  padding: 0 20px;
}

.panel {
  background: #ffffff;
  border: 1px solid #e7e5e4;
  border-radius: 16px;
  padding: 16px 14px 10px;
  margin-bottom: 14px;
}

.tabs-row {
  display: flex;
  gap: 4px;
  padding: 2px 2px 6px;
  overflow-x: auto;
  scrollbar-width: none;
  border-bottom: 1px solid #e7e5e4;
  margin-bottom: 4px;
}
.tabs-row::-webkit-scrollbar {
  display: none;
}

.tab-btn {
  flex-shrink: 0;
  padding: 8px 14px;
  border: none;
  background: transparent;
  color: #a8a29e;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.15s ease;
  position: relative;
}
.tab-btn.active {
  color: #0ea5e9;
  font-weight: 600;
  background: #f0f9ff;
}

.menu-grid {
  padding: 10px 2px 14px;
  position: relative;
  overflow: hidden;
}

.swipe-track {
  display: flex;
  flex-direction: row;
  will-change: transform;
}

.grid-inner {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px 0;
  flex-shrink: 0;
}

.menu-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px 2px;
  cursor: pointer;
  transition: transform 0.1s ease;
}
.menu-item:active {
  transform: scale(0.96);
}

.menu-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  position: relative;
  color: #fff;
}

.icon-svg {
  width: 26px;
  height: 26px;
  color: #fff !important;
  fill: currentColor;
}
.icon-svg svg {
  fill: currentColor;
}

.icon-img {
  width: 28px;
  height: 28px;
  object-fit: contain;
  border-radius: 6px;
}

.icon-emoji {
  line-height: 1;
}

.external-tag {
  position: absolute;
  top: -3px;
  right: -5px;
  font-size: 9px;
  color: #fff;
  background: #f97316;
  padding: 1px 5px;
  border-radius: 6px;
  line-height: 1.3;
  font-weight: 600;
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

.menu-name {
  font-size: 11px;
  color: #57534e;
  white-space: nowrap;
  max-width: 64px;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: center;
}

.empty-hint {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 36px 0;
  color: #d6d3d1;
  font-size: 12px;
}
.empty-hint svg {
  width: 32px;
  height: 32px;
}
</style>