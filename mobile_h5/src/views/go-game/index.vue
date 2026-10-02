<template>
  <div class="game-container">
    <div class="board-panel">
      <canvas ref="canvasRef" class="board-canvas"></canvas>
    </div>

    <aside class="panel">
      <h1>五 子 棋</h1>

      <div class="turn">
        <span class="dot" :class="turnDotClass"></span>
        <span>{{ turnText }}</span>
      </div>
      <div class="meta">第 {{ history.length }} 手</div>

      <div class="divider"></div>

      <div class="label">对局模式</div>
      <div class="row">
        <button :class="{ active: mode === 'pvp' }" @click="setMode('pvp')">双人对战</button>
        <button :class="{ active: mode === 'pve' }" @click="setMode('pve')">人机对战</button>
      </div>

      <div class="label" style="margin-top:16px;">操作</div>
      <div class="row">
        <button @click="undo" :disabled="history.length === 0 || aiThinking">悔棋</button>
        <button @click="resetGame">重新开始</button>
      </div>

      <p class="hint">黑先白后，横、竖、斜任意方向先连成五子者获胜。</p>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const N = 15
const PAD = 40
const CELL = 40
const R = 17
const LOGICAL = 640
const DIRS = [[1, 0], [0, 1], [1, 1], [1, -1]]

const canvasRef = ref(null)
let ctx = null

let board = []
let current = ref(1)
let gameOver = ref(false)
let winner = ref(0)
let winLine = ref(null)
let history = ref([])
let mode = ref('pvp')
let aiThinking = ref(false)
let hoverPos = ref(null)

const turnDotClass = computed(() => {
  if (gameOver.value) {
    return winner.value === 0 ? 'empty' : (winner.value === 1 ? 'black' : 'white')
  }
  return current.value === 1 ? 'black' : 'white'
})

const turnText = computed(() => {
  if (gameOver.value) {
    if (winner.value === 0) return '平局！'
    if (mode.value === 'pve') return winner.value === 1 ? '你赢了！🎉' : 'AI 获胜'
    return (winner.value === 1 ? '黑方' : '白方') + '获胜！'
  }
  if (mode.value === 'pve') return aiThinking.value ? 'AI 思考中…' : (current.value === 1 ? '轮到你（黑）' : 'AI 回合')
  return current.value === 1 ? '黑方回合' : '白方回合'
})

function inBounds(x, y) {
  return x >= 0 && x < N && y >= 0 && y < N
}

function px(i) { return PAD + i * CELL }

function setupCanvas() {
  const canvas = canvasRef.value
  const dpr = Math.min(window.devicePixelRatio || 1, 3)
  canvas.width = LOGICAL * dpr
  canvas.height = LOGICAL * dpr
  ctx = canvas.getContext('2d')
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function draw() {
  const g = ctx.createLinearGradient(0, 0, LOGICAL, LOGICAL)
  g.addColorStop(0, '#f0dcae')
  g.addColorStop(0.45, '#e5c489')
  g.addColorStop(1, '#d6a960')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, LOGICAL, LOGICAL)

  ctx.save()
  ctx.globalAlpha = 0.06
  ctx.strokeStyle = '#6b4614'
  ctx.lineWidth = 1
  for (let i = 0; i < 26; i++) {
    const y = (i * 37) % LOGICAL
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.bezierCurveTo(LOGICAL * 0.3, y + 12, LOGICAL * 0.7, y - 12, LOGICAL, y + 4)
    ctx.stroke()
  }
  ctx.restore()

  const start = PAD
  const end = PAD + (N - 1) * CELL
  ctx.strokeStyle = 'rgba(92, 61, 22, 0.72)'
  ctx.lineWidth = 1
  ctx.beginPath()
  for (let k = 0; k < N; k++) {
    const p = PAD + k * CELL
    ctx.moveTo(start, p); ctx.lineTo(end, p)
    ctx.moveTo(p, start); ctx.lineTo(p, end)
  }
  ctx.stroke()

  ctx.lineWidth = 2.2
  ctx.strokeStyle = 'rgba(78, 50, 16, 0.85)'
  ctx.strokeRect(start, start, end - start, end - start)

  const stars = [[3, 3], [11, 3], [3, 11], [11, 11], [7, 7]]
  ctx.fillStyle = 'rgba(74, 46, 14, 0.9)'
  for (const [sx, sy] of stars) {
    ctx.beginPath()
    ctx.arc(px(sx), px(sy), 4, 0, Math.PI * 2)
    ctx.fill()
  }

  if (hoverPos.value && !gameOver.value && board[hoverPos.value.j][hoverPos.value.i] === 0 && humanCanPlay()) {
    drawStone(px(hoverPos.value.i), px(hoverPos.value.j), current.value, 0.42)
  }

  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      if (board[y][x] !== 0) drawStone(px(x), px(y), board[y][x], 1)
    }
  }

  if (history.value.length && !winLine.value) {
    const last = history.value[history.value.length - 1]
    ctx.beginPath()
    ctx.arc(px(last.i), px(last.j), R * 0.28, 0, Math.PI * 2)
    ctx.fillStyle = last.player === 1 ? 'rgba(255, 90, 90, 0.95)' : 'rgba(220, 60, 60, 0.9)'
    ctx.fill()
  }

  if (winLine.value) {
    ctx.save()
    ctx.strokeStyle = 'rgba(230, 60, 60, 0.95)'
    ctx.lineWidth = 3
    ctx.shadowColor = 'rgba(230, 60, 60, 0.85)'
    ctx.shadowBlur = 12
    for (const p of winLine.value) {
      ctx.beginPath()
      ctx.arc(px(p.x), px(p.y), R + 4.5, 0, Math.PI * 2)
      ctx.stroke()
    }
    ctx.restore()
  }
}

function drawStone(cx, cy, player, alpha) {
  ctx.save()
  if (alpha < 1) ctx.globalAlpha = alpha

  ctx.beginPath()
  ctx.arc(cx + 1.5, cy + 2.5, R, 0, Math.PI * 2)
  ctx.fillStyle = 'rgba(40, 22, 0, 0.3)'
  ctx.fill()

  const grad = ctx.createRadialGradient(
    cx - R * 0.38, cy - R * 0.42, R * 0.12,
    cx, cy, R * 1.15
  )
  if (player === 1) {
    grad.addColorStop(0, '#7d7d7d')
    grad.addColorStop(0.38, '#2f2f2f')
    grad.addColorStop(1, '#050505')
  } else {
    grad.addColorStop(0, '#ffffff')
    grad.addColorStop(0.5, '#f2f2f2')
    grad.addColorStop(1, '#bcbcbc')
  }
  ctx.beginPath()
  ctx.arc(cx, cy, R, 0, Math.PI * 2)
  ctx.fillStyle = grad
  ctx.fill()

  ctx.lineWidth = 1
  ctx.strokeStyle = player === 1 ? 'rgba(0,0,0,.85)' : 'rgba(150,150,150,.7)'
  ctx.stroke()

  ctx.restore()
}

function getGridPos(evt) {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const scale = LOGICAL / rect.width
  const x = (evt.clientX - rect.left) * scale
  const y = (evt.clientY - rect.top) * scale
  const i = Math.round((x - PAD) / CELL)
  const j = Math.round((y - PAD) / CELL)
  if (!inBounds(i, j)) return null
  const dx = x - px(i)
  const dy = y - px(j)
  if (Math.hypot(dx, dy) > CELL * 0.62) return null
  return { i, j }
}

function checkWin(bd, x, y, player) {
  for (const [dx, dy] of DIRS) {
    const line = [{ x, y }]
    for (const sign of [1, -1]) {
      for (let k = 1; k < 5; k++) {
        const nx = x + dx * k * sign
        const ny = y + dy * k * sign
        if (!inBounds(nx, ny) || bd[ny][nx] !== player) break
        line.push({ x: nx, y: ny })
      }
    }
    if (line.length >= 5) return line
  }
  return null
}

function humanCanPlay() {
  if (gameOver.value || aiThinking.value) return false
  if (mode.value === 'pve' && current.value !== 1) return false
  return true
}

function place(i, j) {
  if (gameOver.value || board[j][i] !== 0) return

  board[j][i] = current.value
  history.value.push({ i, j, player: current.value })

  const line = checkWin(board, i, j, current.value)
  if (line) {
    gameOver.value = true
    winner.value = current.value
    winLine.value = line
    draw()
    return
  }

  if (history.value.length === N * N) {
    gameOver.value = true
    winner.value = 0
    draw()
    return
  }

  current.value = 3 - current.value
  draw()

  maybeAI()
}

const PATTERNS = [
  [/11111/, 1000000],
  [/011110/, 100000],
  [/011112|211110/, 12000],
  [/11011|10111|11101/, 12000],
  [/011100|001110/, 4000],
  [/011010|010110/, 4000],
  [/001112|211100/, 1000],
  [/010112|211010/, 1000],
  [/011012|210110/, 1000],
  [/10011|11001|10101/, 1000],
  [/001100/, 500],
  [/001010|010100/, 300],
  [/000100|001000/, 30]
]

function lineAt(bd, x, y, dx, dy, p) {
  let s = ''
  for (let k = -4; k <= 4; k++) {
    const nx = x + dx * k
    const ny = y + dy * k
    if (!inBounds(nx, ny)) s += '2'
    else if (bd[ny][nx] === 0) s += '0'
    else if (bd[ny][nx] === p) s += '1'
    else s += '2'
  }
  return s
}

function pointScore(bd, x, y, p) {
  let total = 0
  for (const [dx, dy] of DIRS) {
    const s = lineAt(bd, x, y, dx, dy, p)
    for (let k = 0; k < PATTERNS.length; k++) {
      if (PATTERNS[k][0].test(s)) {
        total += PATTERNS[k][1]
        break
      }
    }
  }
  return total
}

function getCandidates(bd) {
  const result = []
  const seen = new Set()
  let hasStone = false

  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      if (bd[y][x] === 0) continue
      hasStone = true
      for (let dy = -2; dy <= 2; dy++) {
        for (let dx = -2; dx <= 2; dx++) {
          const nx = x + dx
          const ny = y + dy
          if (!inBounds(nx, ny) || bd[ny][nx] !== 0) continue
          const key = ny * N + nx
          if (seen.has(key)) continue
          seen.add(key)
          result.push({ x: nx, y: ny })
        }
      }
    }
  }

  if (!hasStone) return [{ x: 7, y: 7 }]
  return result
}

function findBestMove(me) {
  const opp = 3 - me
  const cands = getCandidates(board)
  let best = null
  let bestScore = -Infinity

  for (const { x, y } of cands) {
    board[y][x] = me
    const atk = pointScore(board, x, y, me)
    board[y][x] = opp
    const def = pointScore(board, x, y, opp)
    board[y][x] = 0

    const centerBonus = (7 - Math.max(Math.abs(x - 7), Math.abs(y - 7))) * 1.5
    const score = atk * 1.0 + def * 0.85 + centerBonus

    if (score > bestScore) {
      bestScore = score
      best = { x, y }
    }
  }

  return best
}

let aiTimer = null

function maybeAI() {
  if (mode.value !== 'pve' || gameOver.value || current.value !== 2) return

  aiThinking.value = true

  aiTimer = setTimeout(function () {
    if (gameOver.value || current.value !== 2 || mode.value !== 'pve') {
      aiThinking.value = false
      return
    }

    const mv = findBestMove(2)
    aiThinking.value = false

    if (mv) {
      place(mv.x, mv.y)
    }
  }, 280)
}

function resetGame() {
  if (aiTimer) { clearTimeout(aiTimer); aiTimer = null }
  board = Array.from({ length: N }, () => new Array(N).fill(0))
  current.value = 1
  gameOver.value = false
  winner.value = 0
  winLine.value = null
  history.value = []
  hoverPos.value = null
  aiThinking.value = false
  draw()
}

function undo() {
  if (aiThinking.value || history.value.length === 0) return

  gameOver.value = false
  winner.value = 0
  winLine.value = null

  const steps = (mode.value === 'pve' && history.value.length >= 2) ? 2 : 1
  for (let k = 0; k < steps && history.value.length > 0; k++) {
    const m = history.value.pop()
    board[m.j][m.i] = 0
    current.value = m.player
  }

  hoverPos.value = null
  draw()
}

function setMode(m) {
  if (mode.value === m) return
  mode.value = m
  resetGame()
}

function handleClick(e) {
  if (!humanCanPlay()) return
  const pos = getGridPos(e)
  if (!pos) return
  if (board[pos.j][pos.i] !== 0) return
  place(pos.i, pos.j)
}

function handleMouseMove(e) {
  const pos = getGridPos(e)
  const changed = (!!pos !== !!hoverPos.value) ||
    (pos && hoverPos.value && (pos.i !== hoverPos.value.i || pos.j !== hoverPos.value.j))
  hoverPos.value = pos
  if (changed) draw()
}

function handleMouseLeave() {
  if (hoverPos.value) {
    hoverPos.value = null
    draw()
  }
}

onMounted(() => {
  setupCanvas()
  resetGame()

  const canvas = canvasRef.value
  canvas.addEventListener('click', handleClick)
  canvas.addEventListener('mousemove', handleMouseMove)
  canvas.addEventListener('mouseleave', handleMouseLeave)
})

onBeforeUnmount(() => {
  if (aiTimer) clearTimeout(aiTimer)
  const canvas = canvasRef.value
  if (canvas) {
    canvas.removeEventListener('click', handleClick)
    canvas.removeEventListener('mousemove', handleMouseMove)
    canvas.removeEventListener('mouseleave', handleMouseLeave)
  }
})
</script>

<style scoped>
.game-container {
  display: flex;
  gap: 26px;
  align-items: flex-start;
  flex-wrap: wrap;
  justify-content: center;
  padding: 24px;
  min-height: 100vh;
  background: radial-gradient(circle at 28% 18%, #2c3444 0%, #141821 65%);
  color: #e8ecf4;
}

.board-panel {
  width: min(640px, 68vw);
  min-width: 300px;
}

.board-canvas {
  display: block;
  width: 100%;
  height: auto;
  aspect-ratio: 1 / 1;
  border-radius: 10px;
  cursor: pointer;
  box-shadow: 0 24px 60px rgba(0,0,0,.6), 0 0 0 1px rgba(255,255,255,.07);
}

.panel {
  width: 262px;
  flex: 0 0 auto;
  padding: 22px 20px 20px;
  border-radius: 16px;
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.09);
  box-shadow: 0 18px 40px rgba(0,0,0,.35);
  backdrop-filter: blur(10px);
}

h1 {
  margin: 0 0 20px;
  font-size: 19px;
  font-weight: 600;
  letter-spacing: 3px;
  color: #f2f5fb;
}

.turn {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 17px;
  font-weight: 600;
  min-height: 24px;
}

.dot {
  width: 17px;
  height: 17px;
  border-radius: 50%;
  flex: 0 0 auto;
  box-shadow: 0 0 0 1px rgba(255,255,255,.25), inset 0 -1px 2px rgba(0,0,0,.4);
  transition: background .2s;
}
.dot.black { background: radial-gradient(circle at 33% 28%, #6d6d6d, #0a0a0a 70%); }
.dot.white { background: radial-gradient(circle at 33% 28%, #ffffff, #c3c3c3 75%); }
.dot.empty { background: transparent; box-shadow: 0 0 0 2px rgba(255,255,255,.22); }

.meta {
  margin-top: 8px;
  font-size: 12.5px;
  color: #8d99ae;
  letter-spacing: .5px;
}

.divider {
  height: 1px;
  margin: 18px 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.14), transparent);
}

.label {
  font-size: 12px;
  color: #8d99ae;
  letter-spacing: 1px;
  margin-bottom: 9px;
}

.row { display: flex; gap: 8px; }
.row + .row { margin-top: 9px; }

button {
  font-family: inherit;
  font-size: 13.5px;
  padding: 10px 0;
  flex: 1;
  border-radius: 9px;
  border: 1px solid rgba(255,255,255,.14);
  background: rgba(255,255,255,.045);
  color: #cdd6e5;
  cursor: pointer;
  transition: background .16s, color .16s, border-color .16s, transform .08s;
}
button:hover:not(:disabled) { background: rgba(255,255,255,.11); color: #fff; }
button:active:not(:disabled) { transform: translateY(1px); }
button:disabled { opacity: .35; cursor: not-allowed; }

button.active {
  background: linear-gradient(180deg, #4f8cff, #3263d4);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 8px 18px rgba(62,112,240,.4);
}

.hint {
  margin: 18px 0 0;
  font-size: 12px;
  line-height: 1.7;
  color: #77839a;
}

@media (max-width: 760px) {
  .board-panel { width: min(640px, 92vw); }
  .panel { width: min(640px, 92vw); }
}
</style>