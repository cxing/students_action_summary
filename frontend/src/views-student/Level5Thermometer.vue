<template>
  <div class="level-container">
    <div class="level-header">
      <span class="level-badge">第 5 关</span>
      <span class="level-title">🌡️ 温度实验室</span>
      <div class="star-display">
        <span v-for="s in 3" :key="s" :class="s <= store.levels[5].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
      </div>
    </div>

    <div class="game-card">
      <p class="question-text">小宇在做"一壶水加热"实验时，记录了水温变化情况，并制成统计图。请根据统计图填空：</p>

      <div class="chart-container">
        <svg :viewBox="chart.viewBox" class="fill-blank-chart-svg">
          <line v-for="g in chart.gridY" :key="'gy'+g.value" :x1="chart.margin.left" :y1="g.y" :x2="chart.plotRight" :y2="g.y" stroke="#e8e8e8" stroke-width="0.5"/>
          <line v-for="g in chart.gridX" :key="'gx'+g.value" :x1="g.x" :y1="chart.plotTop" :x2="g.x" :y2="chart.plotBottom" stroke="#e8e8e8" stroke-width="0.5"/>
          <line :x1="chart.margin.left" :y1="chart.plotTop" :x2="chart.margin.left" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
          <line :x1="chart.margin.left" :y1="chart.plotBottom" :x2="chart.plotRight" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
          <text v-for="t in chart.yTicks" :key="'yt'+t.value" :x="chart.margin.left - 8" :y="t.y" text-anchor="end" font-size="11" fill="#555" dominant-baseline="middle">{{ t.value }}</text>
          <text v-for="t in chart.xTicks" :key="'xt'+t.value" :x="t.x" :y="chart.plotBottom + 18" text-anchor="middle" font-size="11" fill="#555">{{ t.value }}</text>
          <text :x="14" :y="chart.yLabelY" text-anchor="middle" font-size="13" fill="#333" :transform="'rotate(-90, 14, ' + chart.yLabelY + ')'">水温/℃</text>
          <text :x="chart.margin.left + (chart.plotRight - chart.margin.left) / 2" :y="chart.plotBottom + 36" text-anchor="middle" font-size="13" fill="#333">时间/分</text>
          <polyline :points="chart.linePoints" fill="none" stroke="#4a90d9" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
          <circle v-for="(pt, i) in chart.dataPoints" :key="'dp'+i" :cx="pt.x" :cy="pt.y" r="4" fill="#4a90d9"/>
          <text v-for="(pt, i) in chart.dataPoints" :key="'dt'+i" :x="pt.x" :y="pt.labelY" text-anchor="middle" font-size="10" fill="#333">{{ temps[i] }}</text>
        </svg>
      </div>

      <div class="fill-blank-paragraph">
        <p>
          加热前水温是
          <input type="text" v-model="q5[1]" class="blank-input" @input="onBlankInput" />
          ℃，水加热到 60℃ 时，用了
          <input type="text" v-model="q5[2]" class="blank-input" @input="onBlankInput" />
          分钟，烧开这壶水一共用了
          <input type="text" v-model="q5[3]" class="blank-input" @input="onBlankInput" />
          分钟。如果持续加热到第 16 分钟，此时水温是
          <input type="text" v-model="q5[4]" class="blank-input" @input="onBlankInput" />
          ℃。
        </p>
      </div>

      <div class="thermometer-area">
        <div class="thermometer">
          <div class="thermo-tube">
            <div class="thermo-mercury" :style="{ height: thermoHeight + '%' }"></div>
          </div>
          <div class="thermo-bulb">{{ thermoHeight >= 100 ? '💨' : '🌡️' }}</div>
        </div>
        <div class="thermo-labels">
          <span v-for="t in [100, 80, 60, 40, 20, 0]" :key="t">{{ t }}℃</span>
        </div>
        <div class="thermo-status">
          已填写 {{ filledCount }} / 4 个空
          <span v-if="allCorrect"> — 🎉 全部正确！水烧开了！</span>
          <span v-else-if="filledCount === 4"> — 还有不对的哦，再检查一下折线图上的数据</span>
        </div>
      </div>

      <div class="nav-buttons">
        <router-link to="/level/4" class="btn-secondary">上一关</router-link>
        <router-link to="/submit-success" class="btn-primary">完成闯关！🎉</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useStudentStore } from '../stores/student.js'
import { submitLevel } from '../api.js'

const store = useStudentStore()
const temps = [25, 28, 35, 46, 60, 73, 84, 90, 93, 96, 98, 100]
const correctAnswers = { 1: '25', 2: '4', 3: '11', 4: '100' }
const q5 = reactive({ 1: '', 2: '', 3: '', 4: '' })

onMounted(() => {
  if (store.levels[5].answer) {
    Object.assign(q5, store.levels[5].answer)
  }
})

const filledCount = computed(() => Object.values(q5).filter(v => v.trim() !== '').length)
const allCorrect = computed(() => Object.entries(q5).every(([k, v]) => v.trim() === correctAnswers[k]))

function onBlankInput() {
  if (filledCount.value === 4) submitNow()
}

async function submitNow() {
  const answer = { ...q5 }
  const attempts = store.levels[5].attempts + 1
  const stars = allCorrect.value ? (attempts === 1 ? 3 : attempts === 2 ? 2 : 1) : 0
  store.setLevel(5, { answer, stars, attempts })
  try {
    await submitLevel(store.studentId, 5, answer, stars, attempts)
  } catch (e) { /* continue */ }
}

const thermoHeight = computed(() => {
  const correct = Object.entries(q5).filter(([k, v]) => v.trim() === correctAnswers[k]).length
  return (correct / 4) * 100
})

const chart = computed(() => {
  const margin = { left: 50, top: 20, right: 20, bottom: 40 }
  const plotRight = 660, plotBottom = 420, plotTop = margin.top
  const plotW = plotRight - margin.left, plotH = plotBottom - plotTop
  const xScale = (t) => margin.left + (t / 12) * plotW
  const yScale = (v) => plotBottom - (v / 110) * plotH
  const yTickValues = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
  const xTickValues = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  const gridY = yTickValues.map(v => ({ value: v, y: yScale(v) }))
  const gridX = xTickValues.map(v => ({ value: v, x: xScale(v) }))
  const yTicks = [0, 20, 40, 60, 80, 100].map(v => ({ value: v, y: yScale(v) }))
  const xTicks = [0, 2, 4, 6, 8, 10, 12].map(v => ({ value: v, x: xScale(v) }))
  const dataPoints = temps.map((t, i) => {
    const x = xScale(i), y = yScale(t)
    const offset = i >= 8 ? (i % 2 === 0 ? -14 : 18) : -14
    return { x, y, labelY: y + offset }
  })
  const linePoints = dataPoints.map(p => `${p.x},${p.y}`).join(' ')
  return { viewBox: '0 0 700 480', margin, plotRight, plotTop, plotBottom, gridY, gridX, yTicks, xTicks, dataPoints, linePoints, yLabelY: plotTop + (plotBottom - plotTop) / 2 }
})
</script>
