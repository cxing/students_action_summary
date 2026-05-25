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

      <p class="question-text">小宁在做"一壶水加热"实验时，记录了水温变化情况，并制成统计图。</p>

      <div class="table-section">
        <h4>小宁做一壶水加热实验 — 水温变化统计表</h4>
        <table class="data-table">
          <thead>
            <tr><th v-for="t in times" :key="t">时间/分</th></tr>
            <tr><th v-for="(_, i) in temps" :key="i">{{ i }}</th></tr>
          </thead>
          <tbody>
            <tr><td v-for="t in temps" :key="t">水温/℃</td></tr>
            <tr><td v-for="t in temps" :key="t">{{ t }}</td></tr>
          </tbody>
        </table>
      </div>

      <div class="fill-blank-section">
        <div class="fill-blank-item">
          <label>加热前水温是 <input type="text" v-model="q8[1]" class="blank-input" placeholder="___" /> ℃</label>
        </div>
        <div class="fill-blank-item">
          <label>水加热到 60℃ 时，用了 <input type="text" v-model="q8[2]" class="blank-input" placeholder="___" /> 分钟</label>
        </div>
        <div class="fill-blank-item">
          <label>烧开这壶水一共用了 <input type="text" v-model="q8[3]" class="blank-input" placeholder="___" /> 分钟</label>
        </div>
        <div class="fill-blank-item">
          <label>如果持续加热到第 16 分钟，此时水温是 <input type="text" v-model="q8[4]" class="blank-input" placeholder="___" /> ℃</label>
        </div>
      </div>

      <div class="nav-buttons">
        <button @click="$router.push('/questions')" class="btn-secondary">上一题</button>
        <button @click="goToDrawing" class="btn-primary">
          进入绘图题
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'

const router = useRouter()
const store = useStudentStore()

const temps = [25, 28, 35, 46, 60, 73, 84, 90, 93, 96, 98, 100]
const times = temps.map((_, i) => i)

const q8 = reactive({ 1: '', 2: '', 3: '', 4: '' })

onMounted(() => {
  if (store.fillBlank && store.fillBlank[8]) {
    Object.assign(q8, store.fillBlank[8])
  }
})

function goToDrawing() {
  store.setFillBlank({ 8: { ...q8 } })
  router.push('/drawing')
}
</script>
