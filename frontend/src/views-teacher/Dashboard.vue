<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <h1>折线统计图 — 答题情况</h1>
      <div class="header-actions">
        <span class="teacher-label">教师端</span>
        <button @click="$router.push('/')" class="btn-small">退出</button>
      </div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="dashboard-content">
      <div class="stats-row">
        <div class="stat-card green">
          <span class="stat-number">{{ stats.submitted }} / {{ stats.total }}</span>
          <span class="stat-label">已提交</span>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="dashboard-table">
          <thead>
            <tr>
              <th>姓名</th>
              <th v-for="q in 7" :key="q">Q{{ q }}</th>
              <th>绘图</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in students" :key="s.id">
              <td class="name-cell">{{ s.name }}</td>
              <td v-for="q in 7" :key="q" class="score-cell">
                <span v-if="s.scores[q] === true" class="correct">&#10003;</span>
                <span v-else-if="s.scores[q] === false" class="wrong">&#10007;</span>
                <span v-else class="empty">-</span>
              </td>
              <td class="status-cell">
                <span v-if="s.drawing_submitted" class="correct">&#10003;</span>
                <span v-else class="wrong">&#10007;</span>
              </td>
              <td>
                <router-link :to="'/teacher/student/' + s.id" class="view-link">查看</router-link>
              </td>
            </tr>
            <tr v-if="students.length === 0">
              <td colspan="10" class="empty-row">暂无学生数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDashboard } from '../api.js'

const students = ref([])
const stats = ref({ submitted: 0, total: 0 })
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await getDashboard()
    students.value = res.data.students
    stats.value = res.data.stats
  } catch (e) {
    error.value = '加载失败，请重新登录'
  } finally {
    loading.value = false
  }
})
</script>
