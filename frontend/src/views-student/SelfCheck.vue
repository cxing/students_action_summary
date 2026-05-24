<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
    </div>

    <div class="content-card">
      <h2>自我检查</h2>
      <p class="subtitle">请根据你的学习情况如实完成自我评价</p>

      <div class="check-section">
        <div class="check-item">
          <p>我能说出"点表示数量多少"。</p>
          <label class="check-option"><input type="radio" value="能" v-model="pointCheck" /> 能</label>
          <label class="check-option"><input type="radio" value="还不确定" v-model="pointCheck" /> 还不确定</label>
        </div>

        <div class="check-item">
          <p>我能说出"线表示变化趋势"。</p>
          <label class="check-option"><input type="radio" value="能" v-model="lineCheck" /> 能</label>
          <label class="check-option"><input type="radio" value="还不确定" v-model="lineCheck" /> 还不确定</label>
        </div>

        <div class="check-item">
          <p>我能根据统计表绘制折线统计图。</p>
          <label class="check-option"><input type="radio" value="能" v-model="drawCheck" /> 能</label>
          <label class="check-option"><input type="radio" value="还不确定" v-model="drawCheck" /> 还不确定</label>
        </div>

        <div class="check-item">
          <p>我绘制折线统计图时还需要注意：</p>
          <textarea v-model="note" placeholder="请在此填写..." class="note-input"></textarea>
        </div>
      </div>

      <div class="nav-buttons">
        <button @click="$router.push('/drawing')" class="btn-secondary">返回绘图</button>
        <button @click="submit" class="btn-primary" :disabled="submitting">
          {{ submitting ? '提交中...' : '提交' }}
        </button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'
import { submitAll } from '../api.js'

const router = useRouter()
const store = useStudentStore()

const pointCheck = ref(store.selfCheck.pointCheck || '')
const lineCheck = ref(store.selfCheck.lineCheck || '')
const drawCheck = ref(store.selfCheck.drawCheck || '')
const note = ref(store.selfCheck.note || '')
const submitting = ref(false)
const error = ref('')

async function submit() {
  submitting.value = true
  error.value = ''
  try {
    await submitAll(
      store.studentId,
      store.answers,
      store.drawingPoints,
      { pointCheck: pointCheck.value, lineCheck: lineCheck.value, drawCheck: drawCheck.value, note: note.value }
    )
    router.push('/submit-success')
  } catch (e) {
    error.value = '提交失败，请重试'
  } finally {
    submitting.value = false
  }
}
</script>
