<template>
  <div class="login-page">
    <!-- 装饰元素 -->
    <div class="login-decor login-decor-1">📐</div>
    <div class="login-decor login-decor-2">📏</div>

    <div class="login-card">
      <!-- 学校品牌 -->
      <div class="school-brand">
        <div class="school-icon">🏫</div>
        <div class="school-name">杭州紫金港小学</div>
      </div>

      <!-- 标签 -->
      <div class="login-tag">数 学 课 堂</div>

      <h1 class="page-title">折线统计图</h1>
      <p class="page-subtitle">学 习 单</p>

      <form @submit.prevent="handleLogin" class="login-form">
        <input
          v-model="name"
          type="text"
          placeholder="请输入你的姓名"
          class="name-input"
          autocomplete="off"
        />
        <button type="submit" class="btn-primary-warm" :disabled="!name.trim() || loading">
          {{ loading ? '登录中...' : '开始答题' }}
        </button>
      </form>

      <p v-if="error" class="error">{{ error }}</p>

      <div class="teacher-link">
        <router-link to="/teacher">教师登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'
import { studentLogin } from '../api.js'

const router = useRouter()
const store = useStudentStore()
const name = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!name.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    const res = await studentLogin(name.value.trim())
    const d = res.data
    store.setStudent(d.student_id, d.name)
    if (d.existing_answers) {
      for (const [qno, ans] of Object.entries(d.existing_answers)) {
        store.setAnswer(parseInt(qno), ans)
      }
    }
    if (d.existing_drawing && d.existing_drawing.length > 0) {
      store.setDrawing(d.existing_drawing)
    }
    if (d.existing_self_check) {
      store.setSelfCheck(d.existing_self_check)
    }
    router.push('/preview')
  } catch (e) {
    error.value = '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
