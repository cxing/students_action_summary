<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
      <span class="progress">{{ current + 1 }} / {{ questions.length }}</span>
    </div>

    <div class="content-card">

      <!-- 统计表参考区 -->
      <details class="ref-tables" open>
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
