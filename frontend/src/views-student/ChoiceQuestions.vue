<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
      <span class="progress">{{ current + 1 }} / {{ questions.length }}</span>
    </div>

    <div class="content-card">
      <div class="question-header">
        <span class="question-number">第{{ current + 1 }}题</span>
        <span class="question-type">选择题</span>
      </div>

      <p class="question-text">{{ questions[current].text }}</p>

      <div class="options-list">
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

      <div class="nav-buttons">
        <button v-if="current > 0" @click="prev" class="btn-secondary">上一题</button>
        <span v-else></span>
        <button v-if="current < questions.length - 1" @click="next" class="btn-primary">下一题</button>
        <button v-else @click="goToDrawing" class="btn-primary">进入绘图题</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'

const router = useRouter()
const store = useStudentStore()
const current = ref(0)

const questions = [
  { text: '折线统计图中的"点"表示什么？', options: { A: '数量的多少', B: '图形的颜色', C: '统计图的标题' } },
  { text: '折线统计图中的"线"表示什么？', options: { A: '数量的单位', B: '数量的变化趋势', C: '横轴的长度' } },
  { text: '根据统计表一，要比较6名同学一分钟仰卧起坐个数的多少，最适合用什么统计图？', options: { A: '条形统计图', B: '折线统计图', C: '不需要统计图' } },
  { text: '根据统计表二，要表示许明哲连续6天一分钟仰卧起坐成绩的变化，最适合用什么统计图？', options: { A: '条形统计图', B: '折线统计图', C: '饼图' } },
  { text: '在折线统计图中，如果折线整体向上，通常表示什么？', options: { A: '数量在增加', B: '数量在减少', C: '数量没有变化' } },
  { text: '根据统计表二，许明哲连续6天一分钟仰卧起坐成绩的变化情况是：', options: { A: '成绩整体上升', B: '成绩整体下降', C: '成绩没有变化' } },
  { text: '能否预测许明哲周日的仰卧起坐成绩：', options: { A: '45', B: '50', C: '20' } },
]

function selectAnswer(key) { store.setAnswer(current.value + 1, key) }
function next() { if (current.value < questions.length - 1) current.value++ }
function prev() { if (current.value > 0) current.value-- }
function goToDrawing() { router.push('/drawing') }
</script>
