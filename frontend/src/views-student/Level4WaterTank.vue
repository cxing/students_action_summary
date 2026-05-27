<template>
  <div class="level-container">
    <div class="level-header">
      <span class="level-badge">第 4 关</span>
      <span class="level-title">🧪 水位实验室</span>
      <div class="star-display">
        <span v-for="s in 3" :key="s" :class="s <= store.levels[4].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
      </div>
    </div>

    <div class="game-card">
      <p class="question-text">容器中有一些水，小夏将一根圆柱形铁棒垂直匀速地放入水中，水溢出 800 毫升水。随后又将铁棒匀速取出。下面选项中，正确反映了容器中水位变化情况的是（ ）</p>

      <div class="tank-animation-area">
        <div class="tank-scene">
          <svg viewBox="0 0 300 280" class="tank-svg">
            <rect x="60" y="30" width="180" height="220" fill="none" stroke="#555" stroke-width="2"/>
            <line x1="55" y1="120" x2="245" y2="120" stroke="#e74c3c" stroke-width="1.5" stroke-dasharray="6 3"/>
            <text x="248" y="124" font-size="11" fill="#e74c3c">原始水位</text>
            <rect x="62" y="122" width="176" :height="waterHeight" fill="#4a90d9" opacity="0.5" class="water-fill"/>
            <rect x="135" :y="rodY" width="30" :height="rodHeight" rx="3" fill="#666" class="rod-move"/>
            <text x="150" y="270" text-anchor="middle" font-size="13" fill="#555">容器</text>
          </svg>
        </div>
        <div class="tank-controls">
          <button v-if="tankPhase === 0" @click="playTankAnimation" class="btn-primary play-btn">▶ 播放实验</button>
          <span v-else-if="tankPhase === 1" class="phase-label">⬇ 铁棒放入中...</span>
          <span v-else-if="tankPhase === 2" class="phase-label">💧 水溢出中...</span>
          <span v-else-if="tankPhase === 3" class="phase-label">⬆ 铁棒取出中...</span>
          <span v-else class="phase-label">✅ 实验结束，请选择正确的水位变化图像</span>
        </div>
      </div>

      <div v-if="tankPhase === 4" class="insight-box">
        <strong>💡 思考：</strong>水溢出 800 毫升后，这些水不会回到容器中。铁棒取出后，水位会<span style="color:#e74c3c;font-weight:700;">低于原始水位</span>（红色虚线）。
      </div>

      <div v-if="tankPhase === 4" class="chart-options-grid">
        <label v-for="(desc, key) in chartDescriptions" :key="key"
          class="chart-option"
          :class="{ selected: selectedAnswer === key }"
        >
          <input type="radio" name="q4" :value="key" :checked="selectedAnswer === key" @change="selectAnswer(key)" class="chart-radio"/>
          <div class="chart-label">{{ key }}</div>
          <div class="chart-desc-text">{{ desc }}</div>
          <svg :viewBox="tankCharts[key].viewBox" class="chart-svg">
            <line :x1="tankCharts[key].margin.left" :y1="tankCharts[key].dashedY" :x2="tankCharts[key].plotRight" :y2="tankCharts[key].dashedY" stroke="#e74c3c" stroke-width="1.2" stroke-dasharray="5 3"/>
            <text :x="tankCharts[key].plotRight + 4" :y="tankCharts[key].dashedY + 3" font-size="9" fill="#e74c3c">原水位</text>
            <line v-for="g in tankCharts[key].gridY" :key="'gy'+g.y" :x1="tankCharts[key].margin.left" :y1="g.y" :x2="tankCharts[key].plotRight" :y2="g.y" stroke="#e8e8e8" stroke-width="0.5"/>
            <line :x1="tankCharts[key].margin.left" :y1="tankCharts[key].plotTop" :x2="tankCharts[key].margin.left" :y2="tankCharts[key].plotBottom" stroke="#333" stroke-width="1.2"/>
            <line :x1="tankCharts[key].margin.left" :y1="tankCharts[key].plotBottom" :x2="tankCharts[key].plotRight" :y2="tankCharts[key].plotBottom" stroke="#333" stroke-width="1.2"/>
            <polyline :points="tankCharts[key].linePoints" fill="none" stroke="#4a90d9" stroke-width="2.5" stroke-linejoin="round"/>
            <circle v-for="(pt, i) in tankCharts[key].dataPoints" :key="'dp'+i" :cx="pt.x" :cy="pt.y" r="3.5" fill="#4a90d9"/>
            <text :x="tankCharts[key].margin.left + (tankCharts[key].plotRight - tankCharts[key].margin.left) / 2" :y="tankCharts[key].plotBottom + 24" text-anchor="middle" font-size="10" fill="#555">时间</text>
            <text :x="10" :y="tankCharts[key].plotTop + (tankCharts[key].plotBottom - tankCharts[key].plotTop) / 2" text-anchor="middle" font-size="10" fill="#333" :transform="'rotate(-90, 10, ' + (tankCharts[key].plotTop + (tankCharts[key].plotBottom - tankCharts[key].plotTop) / 2) + ')'">深度</text>
          </svg>
        </label>
      </div>

      <div v-if="feedback" :class="feedback === 'correct' ? 'feedback-correct' : 'feedback-wrong'">
        <template v-if="feedback === 'correct'">🎉 正确！水溢出后不会回来，所以取出铁棒后水位低于原水位（虚线）。</template>
        <template v-else>💡 再想想：水溢出后没有回到容器中，取出铁棒后水面应该低于原来的虚线水位。正确答案是 A。</template>
      </div>

      <div class="nav-buttons">
        <router-link to="/level/3" class="btn-secondary">上一关</router-link>
        <router-link to="/level/5" class="btn-primary">下一关 →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStudentStore } from '../stores/student.js'
import { submitLevel } from '../api.js'

const store = useStudentStore()
const tankPhase = ref(0)
const waterHeight = ref(98)
const rodY = ref(40)
const rodHeight = ref(100)
const selectedAnswer = ref(null)
const feedback = ref(null)

const chartDescriptions = {
  A: '终点低于虚线（原水位）',
  B: '终点继续上升',
  C: '终点回到虚线（原水位）',
  D: '终点高于虚线（原水位）',
}

function playTankAnimation() {
  tankPhase.value = 1
  const downInterval = setInterval(() => {
    rodY.value += 1.5
    rodHeight.value -= 1.5
    if (rodY.value >= 100) {
      clearInterval(downInterval)
      tankPhase.value = 2
      waterHeight.value = 158
      setTimeout(() => {
        tankPhase.value = 3
        const upInterval = setInterval(() => {
          rodY.value -= 1.5
          rodHeight.value += 1.5
          if (rodY.value <= 40) {
            clearInterval(upInterval)
            waterHeight.value = 70
            tankPhase.value = 4
          }
        }, 20)
      }, 1500)
    }
  }, 20)
}

async function selectAnswer(key) {
  selectedAnswer.value = key
  const isCorrect = key === 'A'
  const attempts = store.levels[4].attempts + 1
  const stars = isCorrect ? (attempts === 1 ? 3 : attempts === 2 ? 2 : 1) : 0
  feedback.value = isCorrect ? 'correct' : 'wrong'
  store.setLevel(4, { answer: key, stars, attempts })
  try {
    await submitLevel(store.studentId, 4, key, stars, attempts)
  } catch (e) { /* continue */ }
}

function makeTankChart(timePoints) {
  const margin = { left: 40, top: 15, right: 55, bottom: 35 }
  const viewBox = '0 0 380 280'
  const plotRight = 320, plotBottom = 250, plotTop = margin.top
  const plotW = plotRight - margin.left, plotH = plotBottom - plotTop
  const dashedY = plotBottom - 0.4 * plotH
  const xScale = (t) => margin.left + (t / 6) * plotW
  const yScale = (v) => plotBottom - (v / 100) * plotH * 0.7
  const gridY = [0, 25, 50, 75, 100].map(v => ({ y: yScale(v) }))
  const dataPoints = timePoints.map(([t, v]) => ({ x: xScale(t), y: yScale(v) }))
  const linePoints = dataPoints.map(p => `${p.x},${p.y}`).join(' ')
  return { viewBox, margin, plotRight, plotTop, plotBottom, dashedY, gridY, dataPoints, linePoints }
}

const tankCharts = computed(() => ({
  A: makeTankChart([[0,40],[2,55],[5,55],[6,25]]),
  B: makeTankChart([[0,40],[2,55],[5,55],[6,80]]),
  C: makeTankChart([[0,40],[2,55],[5,55],[6,40]]),
  D: makeTankChart([[0,40],[2,55],[5,55],[6,50]]),
}))
</script>
