<template>
  <div class="login-page">
    <div class="login-card">
      <!-- 学校 Logo 区 -->
      <div class="school-brand">
        <svg class="school-logo" viewBox="0 0 80 80" width="72" height="72">
          <!-- 外圆 -->
          <circle cx="40" cy="40" r="38" fill="none" stroke="#3a7bc8" stroke-width="2.5"/>
          <circle cx="40" cy="40" r="34" fill="#eef4ff" stroke="#3a7bc8" stroke-width="1"/>
          <!-- 打开的书 -->
          <path d="M20 32 L40 28 L60 32 L60 58 L40 54 L20 58 Z" fill="#4a90d9" opacity="0.15" stroke="#3a7bc8" stroke-width="1.8" stroke-linejoin="round"/>
          <line x1="40" y1="28" x2="40" y2="54" stroke="#3a7bc8" stroke-width="1.8"/>
          <!-- 书本横线 -->
          <line x1="28" y1="38" x2="38" y2="36" stroke="#3a7bc8" stroke-width="1" opacity="0.6"/>
          <line x1="28" y1="44" x2="38" y2="42" stroke="#3a7bc8" stroke-width="1" opacity="0.6"/>
          <line x1="42" y1="36" x2="52" y2="38" stroke="#3a7bc8" stroke-width="1" opacity="0.6"/>
          <line x1="42" y1="42" x2="52" y2="44" stroke="#3a7bc8" stroke-width="1" opacity="0.6"/>
          <!-- 顶部装饰 -->
          <circle cx="40" cy="18" r="3" fill="#4a90d9"/>
          <circle cx="28" cy="16" r="2" fill="#7ab8f5" opacity="0.6"/>
          <circle cx="52" cy="16" r="2" fill="#7ab8f5" opacity="0.6"/>
        </svg>
        <div class="school-name">杭州紫金港小学</div>
      </div>

      <h1 class="page-title">折线统计图</h1>
      <p class="page-subtitle">学习单</p>
      <p class="login-hint">请输入你的姓名开始答题</p>

      <form @submit.prevent="handleLogin" class="login-form">
        <input
          v-model="name"
          type="text"
          placeholder="请输入你的姓名"
          class="name-input"
          autocomplete="off"
        />
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
