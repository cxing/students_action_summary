<template>
  <div class="level-container">
    <div class="level-header">
      <span class="level-badge">第 3 关</span>
      <span class="level-title">🚗 汽车行程</span>
      <div class="star-display">
        <span v-for="s in 3" :key="s" :class="s <= store.levels[3].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
      </div>
    </div>

    <div class="game-card">
      <p class="question-text">小明一家周末驾车去湿地公园游玩。汽车以50千米/时的速度行驶1小时到达湿地公园。他们一家在湿地公园玩了3小时后，驾车以原来的速度返回。以下图像中，正确的是（ ）</p>

      <div class="car-animation-area">
        <div class="car-scene">
          <svg viewBox="0 0 600 120" class="car-scene-svg">
            <line x1="0" y1="95" x2="600" y2="95" stroke="#555" stroke-width="2"/>
            <text x="30" y="90" font-size="12" fill="#666">🏠 家</text>
            <text x="270" y="90" font-size="12" fill="#27ae60">🌳 湿地公园</text>
            <g>
              <rect :x="carX" y="70" width="40" height="16" rx="4" fill="#e74c3c"/>
              <circle :cx="carX + 8" cy="88" r="5" fill="#333"/>
              <circle :cx="carX + 32" cy="88" r="5" fill="#333"/>
              <rect :x="carX + 26" y="73" width="10" height="6" rx="1" fill="#aed6f1"/>
            </g>
          </svg>
        </div>
        <div class="car-controls">
          <button v-if="phase === 0" @click="playAnimation" class="btn-primary play-btn">▶ 播放动画</button>
          <span v-else-if="phase === 1" class="phase-label">🚗 行驶中：去公园（1小时，50km）</span>
          <span v-else-if="phase === 2" class="phase-label">🌳 游玩中（3小时）</span>
          <span v-else-if="phase === 3" class="phase-label">🚗 返程中（1小时，50km）</span>
          <span v-else class="phase-label">✅ 动画结束，请选择与动画一致的图像</span>
        </div>
      </div>

      <div v-if="phase === 4" class="chart-options-grid">
        <label
          v-for="(chart, key) in q3Charts"
          :key="key"
          class="chart-option"
          :class="{ selected: selectedAnswer === key }"
        >
          <input type="radio" name="q3" :value="key" :checked="selectedAnswer === key" @change="selectAnswer(key)" class="chart-radio"/>
          <div class="chart-label">{{ key }}</div>
          <svg :viewBox="chart.viewBox" class="chart-svg">
            <line v-for="g in chart.gridY" :key="'gy'+g.y" :x1="chart.margin.left" :y1="g.y" :x2="chart.plotRight" :y2="g.y" stroke="#e8e8e8" stroke-width="0.5"/>
            <line v-for="g in chart.gridX" :key="'gx'+g.x" :x1="g.x" :y1="chart.plotTop" :x2="g.x" :y2="chart.plotBottom" stroke="#e8e8e8" stroke-width="0.5"/>
            <line :x1="chart.margin.left" :y1="chart.plotTop" :x2="chart.margin.left" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
            <line :x1="chart.margin.left" :y1="chart.plotBottom" :x2="chart.plotRight" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
            <text v-for="t in chart.yTicks" :key="'yt'+t.value" :x="chart.margin.left - 6" :y="t.y" text-anchor="end" font-size="10" fill="#555" dominant-baseline="middle">{{ t.value }}</text>
            <text v-for="t in chart.xTicks" :key="'xt'+t.value" :x="t.x" :y="chart.plotBottom + 18" text-anchor="middle" font-size="10" fill="#555">{{ t.value }}</text>
            <text :x="12" :y="chart.plotTop + (chart.plotBottom - chart.plotTop) / 2" text-anchor="middle" font-size="12" fill="#333" :transform="'rotate(-90, 12, ' + (chart.plotTop + (chart.plotBottom - chart.plotTop) / 2) + ')'">{{ chart.yLabel }}</text>
            <text :x="chart.margin.left + (chart.plotRight - chart.margin.left) / 2" :y="chart.plotBottom + 34" text-anchor="middle" font-size="12" fill="#333">{{ chart.xLabel }}</text>
            <polyline :points="chart.linePoints" fill="none" stroke="#4a90d9" stroke-width="2.5" stroke-linejoin="round"/>
            <circle v-for="(pt, i) in chart.dataPoints" :key="'dp'+i" :cx="pt.x" :cy="pt.y" r="3.5" fill="#4a90d9"/>
          </svg>
        </label>
      </div>

      <div v-if="feedback" :class="feedback === 'correct' ? 'feedback-correct' : 'feedback-wrong'">
        {{ feedback === 'correct' ? '🎉 正确！离家后行驶、停留、返回，距离先增后平最后回到0。' : '🤔 这路线不对哦，注意：离家距离变化是：增加→不变→减少到0' }}
      </div>

      <div class="nav-buttons">
        <router-link to="/level/2" class="btn-secondary">上一关</router-link>
        <router-link to="/level/4" class="btn-primary">下一关 →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStudentStore } from '../stores/student.js'
import { submitLevel } from '../api.js'

const store = useStudentStore()
const phase = ref(0)
const carX = ref(30)
const selectedAnswer = ref(null)
const feedback = ref(null)

function playAnimation() {
  phase.value = 1
  const interval = setInterval(() => {
    carX.value += 2.2
    if (carX.value >= 250) {
      carX.value = 250
      clearInterval(interval)
      phase.value = 2
      setTimeout(() => {
        phase.value = 3
        const backInterval = setInterval(() => {
          carX.value -= 2.2
          if (carX.value <= 30) {
            carX.value = 30
            clearInterval(backInterval)
            phase.value = 4
          }
        }, 20)
      }, 2000)
    }
  }, 20)
}

async function selectAnswer(key) {
  selectedAnswer.value = key
  const isCorrect = key === 'D'
  const attempts = store.levels[3].attempts + 1
  const stars = isCorrect ? (attempts === 1 ? 3 : attempts === 2 ? 2 : 1) : 0
  feedback.value = isCorrect ? 'correct' : 'wrong'
  store.setLevel(3, { answer: key, stars, attempts })
  try {
    await submitLevel(store.studentId, 3, key, stars, attempts)
  } catch (e) { /* continue */ }
}

function makeChart(yLabel, timePoints) {
  const margin = { left: 55, top: 18, right: 20, bottom: 35 }
  const viewBox = '0 0 420 300'
  const plotRight = 400, plotBottom = 268, plotTop = margin.top
  const plotW = plotRight - margin.left, plotH = plotBottom - plotTop
  const xScale = (t) => margin.left + (t / 6) * plotW
  const yScale = (v) => plotBottom - (v / 100) * plotH
  const gridY = [0, 25, 50, 75, 100].map(v => ({ y: yScale(v) }))
  const gridX = [0, 1, 2, 3, 4, 5, 6].map(t => ({ x: xScale(t) }))
  const yTicks = [0, 25, 50, 75, 100].map(v => ({ value: v, y: yScale(v) }))
  const xTicks = [0, 1, 2, 3, 4, 5, 6].map(t => ({ value: t, x: xScale(t) }))
  const dataPoints = timePoints.map(([t, v]) => ({ x: xScale(t), y: yScale(v) }))
  const linePoints = dataPoints.map(p => `${p.x},${p.y}`).join(' ')
  return { viewBox, margin, plotRight, plotTop, plotBottom, gridY, gridX, yTicks, xTicks, yLabel: yLabel.replace(/\//g, ' / '), xLabel: '时间/时', dataPoints, linePoints }
}

const q3Charts = computed(() => ({
  A: makeChart('行驶路程/千米', [[0,0],[1,50],[4,50],[5,100],[6,100]]),
  B: makeChart('行驶路程/千米', [[0,0],[1,50],[3,50],[4,100],[6,100]]),
  C: makeChart('离家距离/千米', [[0,0],[1,50],[4,50],[5,100],[6,100]]),
  D: makeChart('离家距离/千米', [[0,0],[1,50],[4,50],[5,25],[6,0]]),
}))
</script>
