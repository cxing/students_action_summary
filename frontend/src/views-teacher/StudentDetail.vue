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
        <h3>答题记录</h3>
        <table class="data-table">
          <thead><tr><th>题号</th><th>子题</th><th>学生答案</th><th>正确答案</th><th>结果</th></tr></thead>
          <tbody>
            <tr v-for="a in detail.answers" :key="a.question_no + '_' + a.sub_no">
              <td>Q{{ a.question_no }}</td>
              <td>{{ a.sub_no > 0 ? '第' + a.sub_no + '空' : '-' }}</td>
              <td>{{ a.answer || '-' }}</td>
              <td>{{ getCorrectAnswer(a.question_no, a.sub_no) }}</td>
              <td :class="a.is_correct ? 'correct' : 'wrong'">{{ a.is_correct ? '✓' : '✗' }}</td>
            </tr>
          </tbody>
        </table>

        <h3 v-if="detail.stars && detail.stars.length > 0" style="margin-top: 20px;">闯关星级</h3>
        <table v-if="detail.stars && detail.stars.length > 0" class="data-table">
          <thead><tr><th>关卡</th><th>星级</th><th>尝试次数</th></tr></thead>
          <tbody>
            <tr v-for="s in detail.stars" :key="s.level_no">
              <td>第{{ s.level_no }}关</td>
              <td>
                <span v-for="i in 3" :key="i" :style="{ color: i <= s.stars ? '#f5a623' : '#ddd' }">&#9733;</span>
                ({{ s.stars }}/3)
              </td>
              <td>{{ s.attempts }} 次</td>
            </tr>
          </tbody>
        </table>
        <p v-if="detail.total_stars !== undefined" style="margin-top: 12px; font-weight: 600;">
          总星数：{{ detail.total_stars }} / 15
        </p>
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

const correctAnswers = {
  1: { 0: 'A' },
  2: { 1: 'A', 2: 'B' },
  3: { 0: 'D' },
  4: { 0: 'A' },
  5: { 1: '25', 2: '4', 3: '11', 4: '100' },
}

function getCorrectAnswer(qno, subNo) {
  const q = correctAnswers[qno]
  if (!q) return '-'
  return q[subNo] || '-'
}

onMounted(async () => {
  try {
    const res = await getStudentDetail(props.id)
    detail.value = res.data
  } catch (e) {
    error.value = '加载失败'
  } finally {
    loading.value = false
  }
})
</script>
