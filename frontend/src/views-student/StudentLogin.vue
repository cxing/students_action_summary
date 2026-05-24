<template>
  <div class="login-container">
    <div class="login-card">
      <h1>折线统计图 学习单</h1>
      <p class="subtitle">请输入你的姓名开始答题</p>
      <form @submit.prevent="handleLogin">
        <input v-model="name" type="text" placeholder="请输入你的姓名" class="name-input" autocomplete="off" />
        <button type="submit" class="btn-primary" :disabled="!name.trim() || loading">
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
    store.setStudent(res.data.student_id, res.data.name)
    router.push('/preview')
  } catch (e) {
    error.value = '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
