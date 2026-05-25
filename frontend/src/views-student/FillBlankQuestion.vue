<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
    </div>

    <div class="content-card">
      <div class="question-header">
        <span class="question-number">第8题</span>
        <span class="question-type">填空题</span>
      </div>

      <p class="question-text">小宇在做"一壶水加热"实验时，记录了水温变化情况，并制成统计图。</p>

      <!-- 水温变化折线图 -->
      <div class="chart-container">
        <svg :viewBox="chart.viewBox" class="fill-blank-chart-svg">
          <!-- 网格线 -->
          <line v-for="g in chart.gridY" :key="'gy'+g.value" :x1="chart.margin.left" :y1="g.y" :x2="chart.plotRight" :y2="g.y" stroke="#e8e8e8" stroke-width="0.5"/>
          <line v-for="g in chart.gridX" :key="'gx'+g.value" :x1="g.x" :y1="chart.plotTop" :x2="g.x" :y2="chart.plotBottom" stroke="#e8e8e8" stroke-width="0.5"/>
          <!-- 坐标轴 -->
          <line :x1="chart.margin.left" :y1="chart.plotTop" :x2="chart.margin.left" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
          <line :x1="chart.margin.left" :y1="chart.plotBottom" :x2="chart.plotRight" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
          <!-- Y轴刻度 & 标签 -->
          <text v-for="t in chart.yTicks" :key="'yt'+t.value" :x="chart.margin.left - 8" :y="t.y" text-anchor="end" font-size="11" fill="#555" dominant-baseline="middle">{{ t.value }}</text>
          <!-- X轴刻度 & 标签 -->
          <text v-for="t in chart.xTicks" :key="'xt'+t.value" :x="t.x" :y="chart.plotBottom + 18" text-anchor="middle" font-size="11" fill="#555">{{ t.value }}</text>
          <!-- Y轴标题 -->
          <text :x="14" :y="chart.yLabelY" text-anchor="middle" font-size="13" fill="#333" :transform="'rotate(-90, 14, ' + chart.yLabelY + ')'">水温/℃</text>
          <!-- X轴标题 -->
          <text :x="chart.margin.left + (chart.plotRight - chart.margin.left) / 2" :y="chart.plotBottom + 36" text-anchor="middle" font-size="13" fill="#333">时间/分</text>
          <!-- 数据折线 -->
          <polyline :points="chart.linePoints" fill="none" stroke="#4a90d9" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
          <!-- 数据点 -->
          <circle v-for="(pt, i) in chart.dataPoints" :key="'dp'+i" :cx="pt.x" :cy="pt.y" r="4" fill="#4a90d9"/>
          <!-- 数据点温度标注 -->
          <text v-for="(pt, i) in chart.dataPoints" :key="'dt'+i" :x="pt.x" :y="pt.labelY" text-anchor="middle" font-size="10" fill="#333">{{ temps[i] }}</text>
        </svg>
      </div>

      <!-- 填空题 - 段落式布局 -->
      <div class="fill-blank-paragraph">
        <p>
          加热前水温是
          <input type="text" v-model="q8[1]" class="blank-input" />
          ℃，水加热到 60℃ 时，用了
          <input type="text" v-model="q8[2]" class="blank-input" />
          分钟，烧开这壶水一共用了
          <input type="text" v-model="q8[3]" class="blank-input" />
          分钟。如果持续加热到第 16 分钟，此时水温是
          <input type="text" v-model="q8[4]" class="blank-input" />
          ℃。
        </p>
      </div>

      <div class="nav-buttons">
        <button @click="$router.push('/questions')" class="btn-secondary">上一题</button>
        <button @click="goToSelfCheck" class="btn-primary">
          进入自我检查
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'

const router = useRouter()
const store = useStudentStore()

const temps = [25, 28, 35, 46, 60, 73, 84, 90, 93, 96, 98, 100]

const q8 = reactive({ 1: '', 2: '', 3: '', 4: '' })

onMounted(() => {
  if (store.fillBlank && store.fillBlank[8]) {
    Object.assign(q8, store.fillBlank[8])
  }
})

function goToSelfCheck() {
  store.setFillBlank({ 8: { ...q8 } })
  router.push('/self-check')
}

// 折线图配置
const chart = computed(() => {
  const margin = { left: 50, top: 20, right: 20, bottom: 40 }
  const plotRight = 660
  const plotBottom = 420
  const plotTop = margin.top
  const plotW = plotRight - margin.left
  const plotH = plotBottom - plotTop

  const xScale = (t) => margin.left + (t / 12) * plotW
  const yScale = (v) => plotBottom - (v / 110) * plotH

  const yTickValues = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
  const xTickValues = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

  const gridY = yTickValues.map(v => ({ value: v, y: yScale(v) }))
  const gridX = xTickValues.map(v => ({ value: v, x: xScale(v) }))
  const yTicks = [0, 20, 40, 60, 80, 100].map(v => ({ value: v, y: yScale(v) }))
  const xTicks = [0, 2, 4, 6, 8, 10, 12].map(v => ({ value: v, x: xScale(v) }))

  const dataPoints = temps.map((t, i) => {
    const x = xScale(i)
    const y = yScale(t)
    // 密集区 (i>=8) 交替上下偏移，避免标签重叠
    const offset = i >= 8 ? (i % 2 === 0 ? -14 : 18) : -14
    return { x, y, labelY: y + offset }
  })
  const linePoints = dataPoints.map(p => `${p.x},${p.y}`).join(' ')

  return {
    viewBox: '0 0 700 480',
    margin, plotRight, plotTop, plotBottom,
    gridY, gridX, yTicks, xTicks,
    dataPoints, linePoints,
    yLabelY: plotTop + (plotBottom - plotTop) / 2,
  }
})
</script>
