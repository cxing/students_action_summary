<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
      <span class="progress">{{ current + 1 }} / {{ questions.length }}</span>
    </div>

    <div class="content-card">

      <!-- 统计表参考区（仅 Q1-Q6 显示） -->
      <details v-if="current < 6" class="ref-tables" open>
        <summary>统计数据参考（点击收起/展开）</summary>
        <div class="table-section">
          <h4>统计表一：6名同学一分钟仰卧起坐个数统计表</h4>
          <table class="data-table">
            <thead><tr><th>姓名</th><th>周子昂</th><th>许明哲</th><th>沈嘉诚</th><th>叶思涵</th><th>李欣怡</th><th>吴俊杰</th></tr></thead>
            <tbody><tr><td>个数/个</td><td>35</td><td>42</td><td>38</td><td>40</td><td>36</td><td>33</td></tr></tbody>
          </table>
        </div>
        <div class="table-section">
          <h4>统计表二：许明哲连续6天一分钟仰卧起坐成绩统计表</h4>
          <table class="data-table">
            <thead><tr><th>日期</th><th>周一</th><th>周二</th><th>周三</th><th>周四</th><th>周五</th><th>周六</th></tr></thead>
            <tbody><tr><td>个数/个</td><td>30</td><td>32</td><td>35</td><td>36</td><td>39</td><td>42</td></tr></tbody>
          </table>
        </div>
      </details>

      <div class="question-header">
        <span class="question-number">第{{ current + 1 }}题</span>
        <span class="question-type">选择题</span>
      </div>

      <p class="question-text">{{ questions[current].text }}</p>

      <!-- Q1-Q6: 文字选项 -->
      <div v-if="current < 6" class="options-list">
        <label
          v-for="(opt, key) in questions[current].options"
          :key="key"
          class="option-item"
          :class="{ selected: store.answers[current + 1] === key }"
        >
          <input
            type="radio"
            :name="'q' + current"
            :value="key"
            :checked="store.answers[current + 1] === key"
            @change="selectAnswer(key)"
          />
          <span class="option-label">{{ key }}. {{ opt }}</span>
        </label>
      </div>

      <!-- Q7: 折线图选项 2x2 网格 -->
      <div v-else class="chart-options-grid">
        <label
          v-for="(chart, key) in q7Charts"
          :key="key"
          class="chart-option"
          :class="{ selected: store.answers[7] === key }"
        >
          <input
            type="radio"
            name="q7"
            :value="key"
            :checked="store.answers[7] === key"
            @change="selectAnswer(key)"
            class="chart-radio"
          />
          <div class="chart-label">{{ key }}</div>
          <svg :viewBox="chart.viewBox" class="chart-svg">
            <!-- 网格线 -->
            <line v-for="g in chart.gridY" :key="'gy'+g.y" :x1="chart.margin.left" :y1="g.y" :x2="chart.plotRight" :y2="g.y" stroke="#e8e8e8" stroke-width="0.5"/>
            <line v-for="g in chart.gridX" :key="'gx'+g.x" :x1="g.x" :y1="chart.plotTop" :x2="g.x" :y2="chart.plotBottom" stroke="#e8e8e8" stroke-width="0.5"/>
            <!-- 坐标轴 -->
            <line :x1="chart.margin.left" :y1="chart.plotTop" :x2="chart.margin.left" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
            <line :x1="chart.margin.left" :y1="chart.plotBottom" :x2="chart.plotRight" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
            <!-- Y轴刻度 & 标签 -->
            <text v-for="t in chart.yTicks" :key="'yt'+t.value" :x="chart.margin.left - 6" :y="t.y" text-anchor="end" font-size="10" fill="#555" dominant-baseline="middle">{{ t.value }}</text>
            <!-- X轴刻度 & 标签 -->
            <text v-for="t in chart.xTicks" :key="'xt'+t.value" :x="t.x" :y="chart.plotBottom + 18" text-anchor="middle" font-size="10" fill="#555">{{ t.value }}</text>
            <!-- Y轴标题 -->
            <text :x="12" :y="chart.plotTop + (chart.plotBottom - chart.plotTop) / 2" text-anchor="middle" font-size="12" fill="#333" :transform="'rotate(-90, 12, ' + (chart.plotTop + (chart.plotBottom - chart.plotTop) / 2) + ')'">{{ chart.yLabel }}</text>
            <!-- X轴标题 -->
            <text :x="chart.margin.left + (chart.plotRight - chart.margin.left) / 2" :y="chart.plotBottom + 34" text-anchor="middle" font-size="12" fill="#333">{{ chart.xLabel }}</text>
            <!-- 数据折线 -->
            <polyline :points="chart.linePoints" fill="none" stroke="#4a90d9" stroke-width="2.5" stroke-linejoin="round"/>
            <!-- 数据点 -->
            <circle v-for="(pt, i) in chart.dataPoints" :key="'dp'+i" :cx="pt.x" :cy="pt.y" r="3.5" fill="#4a90d9"/>
          </svg>
        </label>
      </div>

      <div class="nav-buttons">
        <button v-if="current > 0" @click="prev" class="btn-secondary">上一题</button>
        <span v-else></span>
        <button
          v-if="current < questions.length - 1"
          @click="next"
          class="btn-primary"
          :disabled="!hasAnswered"
        >
          {{ hasAnswered ? '下一题' : '请先选择答案' }}
        </button>
        <button
          v-else
          @click="goToFillBlank"
          class="btn-primary"
          :disabled="!hasAnswered"
        >
          {{ hasAnswered ? '进入填空题' : '请先选择答案' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'

const router = useRouter()
const store = useStudentStore()
const current = ref(0)

const hasAnswered = computed(() => store.answers[current.value + 1] != null)

const questions = [
  { text: '折线统计图中的"点"表示什么？', options: { A: '数量的多少', B: '图形的颜色', C: '统计图的标题' } },
  { text: '折线统计图中的"线"表示什么？', options: { A: '数量的单位', B: '数量的变化趋势', C: '横轴的长度' } },
  { text: '根据统计表一，要比较6名同学一分钟仰卧起坐个数的多少，最适合用什么统计图？', options: { A: '条形统计图', B: '折线统计图', C: '不需要统计图' } },
  { text: '根据统计表二，要表示许明哲连续6天一分钟仰卧起坐成绩的变化，最适合用什么统计图？', options: { A: '条形统计图', B: '折线统计图', C: '饼图' } },
  { text: '在折线统计图中，如果折线整体向上，通常表示什么？', options: { A: '数量在增加', B: '数量在减少', C: '数量没有变化' } },
  { text: '根据统计表二，许明哲连续6天一分钟仰卧起坐成绩的变化情况是：', options: { A: '成绩整体上升', B: '成绩整体下降', C: '成绩没有变化' } },
  { text: '小明一家周末驾车去湿地公园游玩。汽车以50千米/时的速度行驶1小时到达湿地公园。他们一家在湿地公园玩了3小时后，驾车以原来的速度返回。以下图像中，正确的是（ ）', options: {
    A: '',
    B: '',
    C: '',
    D: '',
  } },
]

function selectAnswer(key) { store.setAnswer(current.value + 1, key) }
function next() { if (current.value < questions.length - 1) current.value++ }
function prev() { if (current.value > 0) current.value-- }
function goToFillBlank() { router.push('/fill-blank') }

// Q7 四个折线图的数据配置
function makeChart(yLabel, timePoints) {
  const margin = { left: 55, top: 18, right: 20, bottom: 35 }
  const viewBox = '0 0 420 300'
  const plotRight = 400
  const plotBottom = 268
  const plotTop = margin.top
  const plotW = plotRight - margin.left
  const plotH = plotBottom - plotTop

  const xScale = (t) => margin.left + (t / 6) * plotW
  const yScale = (v) => plotBottom - (v / 100) * plotH

  const gridY = [0, 25, 50, 75, 100].map(v => ({ y: yScale(v) }))
  const gridX = [0, 1, 2, 3, 4, 5, 6].map(t => ({ x: xScale(t) }))
  const yTicks = [0, 25, 50, 75, 100].map(v => ({ value: v, y: yScale(v) }))
  const xTicks = [0, 1, 2, 3, 4, 5, 6].map(t => ({ value: t, x: xScale(t) }))

  const dataPoints = timePoints.map(([t, v]) => ({ x: xScale(t), y: yScale(v) }))
  const linePoints = dataPoints.map(p => `${p.x},${p.y}`).join(' ')

  return {
    viewBox, margin, plotRight, plotTop, plotBottom,
    gridY, gridX, yTicks, xTicks,
    yLabel: yLabel.replace(/\//g, ' / '),
    xLabel: '时间/时',
    dataPoints, linePoints,
  }
}

const q7Charts = computed(() => ({
  A: makeChart('行驶路程/千米', [[0,0],[1,50],[4,50],[5,100],[6,100]]),
  B: makeChart('行驶路程/千米', [[0,0],[1,50],[3,50],[4,100],[6,100]]),
  C: makeChart('离家距离/千米', [[0,0],[1,50],[4,50],[5,100],[6,100]]),
  D: makeChart('离家距离/千米', [[0,0],[1,50],[4,50],[5,25],[6,0]]),
}))
</script>
