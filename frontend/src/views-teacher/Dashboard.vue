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
      <div v-if="deleteMsg" :class="deleteOk ? 'success-msg' : 'error-msg'">{{ deleteMsg }}</div>

      <div class="stats-row">
        <div class="stat-card green">
          <span class="stat-number">{{ stats.submitted }} / {{ stats.total }}</span>
          <span class="stat-label">已提交</span>
        </div>
      </div>

      <div class="chart-section">
        <h3>📊 统计图生成</h3>
        <div class="chart-buttons">
          <button @click="showChart('questions')" class="btn-secondary">各题正确率柱状图</button>
          <button @click="showChart('stars')" class="btn-secondary">星星分布柱状图</button>
        </div>
        <div v-if="chartSrc" class="chart-preview">
          <img :src="chartSrc" alt="统计图" />
          <br/>
          <a :href="chartSrc" download class="btn-small" style="margin-top:8px;display:inline-block;">下载图片</a>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="dashboard-table">
          <thead>
            <tr>
              <th>姓名</th>
              <th v-for="q in 5" :key="q">Q{{ q }}</th>
              <th>星星</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in students" :key="s.id">
              <td class="name-cell">{{ s.name }}</td>
              <td v-for="q in 5" :key="q" class="score-cell">
                <span v-if="q === 5">
                  <span v-if="getQ5Summary(s) !== null" :class="getQ5Summary(s) === 4 ? 'correct' : 'wrong'">{{ getQ5Summary(s) }}/4</span>
                  <span v-else class="empty">-</span>
                </span>
                <span v-else-if="q === 2">
                  <span v-if="getQ2Summary(s) !== null" :class="getQ2Summary(s) === 2 ? 'correct' : 'wrong'">{{ getQ2Summary(s) }}/2</span>
                  <span v-else class="empty">-</span>
                </span>
                <span v-else>
                  <span v-if="s.scores[q] === true" class="correct">&#10003;</span>
                  <span v-else-if="s.scores[q] === false" class="wrong">&#10007;</span>
                  <span v-else class="empty">-</span>
                </span>
              </td>
              <td class="score-cell">
                <span v-if="s.total_stars > 0" class="correct">{{ s.total_stars }}/15</span>
                <span v-else class="empty">-</span>
              </td>
              <td class="action-cell">
                <router-link :to="'/teacher/student/' + s.id" class="view-link">查看</router-link>
                <button @click="confirmDelete(s)" class="btn-delete">删除</button>
              </td>
            </tr>
            <tr v-if="students.length === 0">
              <td colspan="8" class="empty-row">暂无学生数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showConfirm" class="modal-overlay" @click.self="showConfirm = false">
      <div class="modal-card">
        <h3>确认删除</h3>
        <p>确定要删除 <strong>{{ deleteTarget?.name }}</strong> 的所有数据吗？</p>
        <p class="modal-hint">此操作不可撤销，将清除该学生的全部记录。</p>
        <div class="modal-buttons">
          <button @click="showConfirm = false" class="btn-secondary">取消</button>
          <button @click="doDelete" class="btn-danger" :disabled="deleting">
            {{ deleting ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDashboard, deleteStudentSubmission } from '../api.js'

const students = ref([])
const stats = ref({ submitted: 0, total: 0 })
const loading = ref(true)
const error = ref('')

const showConfirm = ref(false)
const deleteTarget = ref(null)
const deleting = ref(false)
const deleteMsg = ref('')
const deleteOk = ref(false)

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

const chartSrc = ref('')

function getQ2Summary(s) {
  const keys = ['2_1', '2_2']
  const hasAny = keys.some(k => k in s.scores)
  if (!hasAny) return null
  return keys.filter(k => s.scores[k] === true).length
}

function getQ5Summary(s) {
  const keys = ['5_1', '5_2', '5_3', '5_4']
  const hasAny = keys.some(k => k in s.scores)
  if (!hasAny) return null
  return keys.filter(k => s.scores[k] === true).length
}

function showChart(type) {
  chartSrc.value = `/api/teacher/chart?type=${type}&t=${Date.now()}`
}

function confirmDelete(student) {
  deleteTarget.value = student
  showConfirm.value = true
}

async function doDelete() {
  deleting.value = true
  deleteMsg.value = ''
  const targetId = deleteTarget.value.id
  const targetName = deleteTarget.value.name
  try {
    await deleteStudentSubmission(targetId)
    showConfirm.value = false
    deleteTarget.value = null
    // Refresh dashboard
    const res = await getDashboard()
    students.value = res.data.students
    stats.value = res.data.stats
    deleteOk.value = true
    deleteMsg.value = `已删除 ${targetName} 的答题提交`
  } catch (e) {
    showConfirm.value = false
    deleteOk.value = false
    const detail = e.response?.data?.error || e.message || '请重试'
    deleteMsg.value = `删除失败：${detail}`
  } finally {
    deleting.value = false
  }
}
</script>
