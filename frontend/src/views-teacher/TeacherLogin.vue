<template>
  <div class="login-page-blue">
    <!-- 装饰圆 -->
    <div class="blue-decor blue-decor-1"></div>
    <div class="blue-decor blue-decor-2"></div>

    <!-- 学校品牌（深蓝区域） -->
    <div class="school-hero">
      <div class="school-logo-circle">📖</div>
      <div class="school-name-light">紫金港小学</div>
    </div>

    <div class="login-card">
      <h1 class="page-title">教师登录</h1>

      <form @submit.prevent="handleLogin" class="login-form">
        <input v-model="username" type="text" placeholder="用户名" class="name-input" autocomplete="off" />
        <input v-model="password" type="password" placeholder="密码" class="name-input" />
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <p v-if="error" class="error">{{ error }}</p>

      <div class="teacher-link">
        <router-link to="/">返回学生登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTeacherStore } from '../stores/teacher.js'
import { teacherLogin } from '../api.js'

const router = useRouter()
const teacherStore = useTeacherStore()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await teacherLogin(username.value, password.value)
    teacherStore.setLoggedIn(true)
    router.push('/teacher/dashboard')
  } catch (e) {
    error.value = e.response?.data?.error || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>
