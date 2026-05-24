<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <h1>{{ detail?.name }} · 答题详情</h1>
      <router-link to="/teacher/dashboard" class="btn-small">← 返回概览</router-link>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="detail" class="detail-content">
      <div class="content-card">
        <h3>选择题答案</h3>
        <table class="data-table">
          <thead><tr><th>题号</th><th>学生答案</th><th>正确答案</th><th>结果</th></tr></thead>
          <tbody>
            <tr v-for="a in detail.answers" :key="a.question_no">
              <td>{{ a.question_no }}</td>
              <td>{{ a.answer || '-' }}</td>
              <td>{{ correctAnswers[a.question_no] }}</td>
              <td :class="a.is_correct ? 'correct' : 'wrong'">{{ a.is_correct ? '✓' : '✗' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="content-card" v-if="detail.drawing">
        <h3>绘图题</h3>
        <div class="drawing-review">
          <canvas ref="reviewCanvas" :width="440" :height="300" class="review-canvas"></canvas>
        </div>
        <div class="drawing-score">
          <span :class="detail.drawing.auto_score.points_correct ? 'correct' : 'wrong'">
            {{ detail.drawing.auto_score.points_correct ? '✓' : '✗' }} 描点正确
          </span>
          <span :class="detail.drawing.auto_score.in_order ? 'correct' : 'wrong'">
            {{ detail.drawing.auto_score.in_order ? '✓' : '✗' }} 按序连线
          </span>
          <span>趋势：{{ detail.drawing.auto_score.trend }}</span>
        </div>
      </div>

      <div class="content-card" v-if="detail.self_check">
        <h3>自我检查</h3>
        <p>"点表示数量多少" — {{ detail.self_check.point_check || '未填' }}</p>
        <p>"线表示变化趋势" — {{ detail.self_check.line_check || '未填' }}</p>
        <p>"能绘制折线统计图" — {{ detail.self_check.draw_check || '未填' }}</p>
        <p v-if="detail.self_check.note">还需注意：{{ detail.self_check.note }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStudentDetail } from '../api.js'

const props = defineProps({ id: String })
const detail = ref(null)
const loading = ref(true)
const error = ref('')
const reviewCanvas = ref(null)
const correctAnswers = { 1: 'A', 2: 'B', 3: 'A', 4: 'B', 5: 'A', 6: 'A', 7: 'A' }

onMounted(async () => {
  try {
    const res = await getStudentDetail(props.id)
    detail.value = res.data
    if (detail.value.drawing) {
      setTimeout(() => drawReviewCanvas(), 50)
    }
  } catch (e) {
    error.value = '加载失败'
  } finally {
    loading.value = false
  }
})

function drawReviewCanvas() {
  const canvas = reviewCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const dayLabels = ['周一', '周二', '周三', '周四', '周五', '周六']
  const w = 440, h = 300
  const pad = { top: 15, right: 20, bottom: 28, left: 32 }
  const pw = w - pad.left - pad.right
  const ph = h - pad.top - pad.bottom

  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, w, h)

  // Y-axis grid lines and labels
  ctx.strokeStyle = '#e8e8e8'
  ctx.lineWidth = 0.5
  ctx.fillStyle = '#888'
  ctx.font = '10px sans-serif'
  ctx.textAlign = 'right'
  for (let val = 0; val <= 45; val += 5) {
    const y = pad.top + ph - (val / 45) * ph
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(pad.left + pw, y); ctx.stroke()
    ctx.fillText(val, pad.left - 4, y + 3)
  }

  // X-axis grid lines and labels
  ctx.textAlign = 'center'
  for (let i = 0; i < 6; i++) {
    const x = pad.left + (i / 5) * pw
    ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, pad.top + ph); ctx.stroke()
    ctx.fillText(dayLabels[i], x, pad.top + ph + 16)
  }

  // Axes
  ctx.strokeStyle = '#333'
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.moveTo(pad.left, pad.top)
  ctx.lineTo(pad.left, pad.top + ph)
  ctx.lineTo(pad.left + pw, pad.top + ph)
  ctx.stroke()

  const points = detail.value.drawing.points
  if (!points || points.length === 0) return

  // Only draw line if all 6 points present
  if (points.length === 6) {
    ctx.strokeStyle = '#e74c3c'
    ctx.lineWidth = 2
    ctx.beginPath()
    const sorted = [...points].sort((a, b) => a[0] - b[0])
    sorted.forEach((pt, i) => {
      const day = pt[0], val = pt[1]
      const x = pad.left + (day / 5) * pw
      const y = pad.top + ph - (val / 45) * ph
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    })
    ctx.stroke()
  }

  points.forEach(pt => {
    const day = pt[0], val = pt[1]
    const x = pad.left + (day / 5) * pw
    const y = pad.top + ph - (val / 45) * ph
    ctx.fillStyle = '#e74c3c'
    ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill()
    ctx.fillStyle = '#333'
    ctx.font = 'bold 10px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(val, x, y - 8)
  })
}
</script>
