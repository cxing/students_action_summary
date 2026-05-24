<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
    </div>

    <div class="content-card">
      <h2>题目7（绘图题）</h2>
      <p class="subtitle">根据统计表二，在下方方格图中绘制"许明哲连续6天一分钟仰卧起坐成绩折线统计图"。</p>

      <div class="drawing-requirements">
        <span>要求：</span>①准确描点 ②在点旁标出数据 ③按时间顺序连线 ④观察趋势
      </div>

      <details class="ref-tables">
        <summary>统计数据参考（点击收起/展开）</summary>
        <div class="table-section">
          <h4>统计表二：许明哲连续6天一分钟仰卧起坐成绩统计表</h4>
          <table class="data-table">
            <thead><tr><th>日期</th><th>周一</th><th>周二</th><th>周三</th><th>周四</th><th>周五</th><th>周六</th></tr></thead>
            <tbody><tr><td>个数/个</td><td>30</td><td>32</td><td>35</td><td>36</td><td>39</td><td>42</td></tr></tbody>
          </table>
        </div>
      </details>

      <div class="canvas-wrapper">
        <div class="y-axis-label">个数/个</div>
        <canvas
          ref="canvasRef"
          :width="canvasWidth"
          :height="canvasHeight"
          @click="handleCanvasClick"
          class="drawing-canvas"
        ></canvas>
        <div class="x-axis-labels">
          <span v-for="day in dayLabels" :key="day" :class="{ active: plottedValue(dayLabels.indexOf(day)) !== null }">{{ day }}</span>
        </div>
      </div>

      <div class="drawing-info">
        <span class="plot-count">已描点：{{ plottedCount }} / 6</span>
        <span v-if="plottedCount === 6" class="trend-badge">趋势：{{ trendText }}</span>
      </div>

      <div class="nav-buttons">
        <button @click="resetDrawing" class="btn-secondary">重新描点</button>
        <button @click="goToSelfCheck" class="btn-primary" :disabled="plottedCount < 6">
          {{ plottedCount < 6 ? `还有 ${6 - plottedCount} 个点未描` : '完成绘图，继续' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'

const router = useRouter()
const store = useStudentStore()

const dayLabels = ['周一', '周二', '周三', '周四', '周五', '周六']

// Canvas dimensions
const canvasWidth = 640
const canvasHeight = 420
const canvasRef = ref(null)

// Plot area padding
const padding = { top: 20, right: 30, bottom: 10, left: 40 }
const plotWidth = canvasWidth - padding.left - padding.right
const plotHeight = canvasHeight - padding.top - padding.bottom

// Plotted points as {x, y, value} where x,y are canvas coords
const plottedPoints = ref([])

const plottedCount = computed(() => plottedPoints.value.length)

const trendText = computed(() => {
  if (plottedPoints.value.length < 6) return ''
  const vals = plottedPoints.value.map(p => p.value)
  for (let i = 1; i < vals.length; i++) {
    if (vals[i] <= vals[i - 1]) return '需检查'
  }
  return '整体上升'
})

function valueToY(val) { return padding.top + plotHeight - (val / 45) * plotHeight }
function dayToX(dayIndex) { return padding.left + (dayIndex / 5) * plotWidth }
function yToValue(y) { return Math.round(((padding.top + plotHeight - y) / plotHeight) * 45) }

function plottedValue(dayIndex) {
  const pt = plottedPoints.value[dayIndex]
  return pt ? pt.value : null
}

function drawGrid() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvasWidth, canvasHeight)

  // Background
  ctx.fillStyle = '#fafbfc'
  ctx.fillRect(0, 0, canvasWidth, canvasHeight)

  // Plot area background
  ctx.fillStyle = '#fff'
  ctx.fillRect(padding.left, padding.top, plotWidth, plotHeight)

  // Y-axis grid lines and labels
  ctx.strokeStyle = '#e8e8e8'
  ctx.lineWidth = 1
  ctx.fillStyle = '#888'
  ctx.font = '12px sans-serif'
  ctx.textAlign = 'right'
  for (let val = 0; val <= 45; val += 5) {
    const y = valueToY(val)
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(padding.left + plotWidth, y)
    ctx.stroke()
    ctx.fillText(val, padding.left - 6, y + 4)
  }

  // X-axis grid lines
  ctx.textAlign = 'center'
  for (let i = 0; i < 6; i++) {
    const x = dayToX(i)
    ctx.strokeStyle = '#e8e8e8'
    ctx.beginPath()
    ctx.moveTo(x, padding.top)
    ctx.lineTo(x, padding.top + plotHeight)
    ctx.stroke()
  }

  // Axes
  ctx.strokeStyle = '#333'
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.moveTo(padding.left, padding.top)
  ctx.lineTo(padding.left, padding.top + plotHeight)
  ctx.lineTo(padding.left + plotWidth, padding.top + plotHeight)
  ctx.stroke()

  // Plot line connecting all points
  if (plottedPoints.value.length >= 2) {
    ctx.strokeStyle = '#e74c3c'
    ctx.lineWidth = 2.5
    ctx.lineJoin = 'round'
    ctx.beginPath()
    for (let i = 0; i < plottedPoints.value.length; i++) {
      const pt = plottedPoints.value[i]
      if (i === 0) ctx.moveTo(pt.x, pt.y)
      else ctx.lineTo(pt.x, pt.y)
    }
    ctx.stroke()
  }

  // Plot points and labels
  for (let i = 0; i < plottedPoints.value.length; i++) {
    const pt = plottedPoints.value[i]
    ctx.fillStyle = '#e74c3c'
    ctx.beginPath()
    ctx.arc(pt.x, pt.y, 6, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()
    ctx.fillStyle = '#333'
    ctx.font = 'bold 14px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(pt.value, pt.x, pt.y - 14)
  }
}

function handleCanvasClick(e) {
  if (plottedPoints.value.length >= 6) return

  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvasWidth / rect.width
  const scaleY = canvasHeight / rect.height
  const clickY = (e.clientY - rect.top) * scaleY

  // Determine which day this click is for (sequential)
  const dayIndex = plottedPoints.value.length

  // Snap X to the day's vertical grid line
  const x = dayToX(dayIndex)
  // Clamp Y and round to nearest grid line (5-unit increments)
  const clampedY = Math.max(padding.top, Math.min(padding.top + plotHeight, clickY))
  const snappedValue = Math.round(yToValue(clampedY) / 5) * 5
  const snappedY = valueToY(Math.min(45, Math.max(0, snappedValue)))

  plottedPoints.value.push({ x, y: snappedY, value: snappedValue })

  // Store as [dayIndex, value] for submission
  const drawingData = plottedPoints.value.map((p, i) => [i, p.value])
  store.setDrawing(drawingData)

  drawGrid()
}

function resetDrawing() {
  plottedPoints.value = []
  store.setDrawing([])
  drawGrid()
}

function goToSelfCheck() {
  router.push('/self-check')
}

onMounted(() => {
  // Restore previously plotted points from store (for back-navigation)
  if (store.drawingPoints && store.drawingPoints.length > 0) {
    for (const [dayIndex, value] of store.drawingPoints) {
      const x = dayToX(dayIndex)
      const y = valueToY(value)
      plottedPoints.value.push({ x, y, value })
    }
  }
  drawGrid()
})
</script>
