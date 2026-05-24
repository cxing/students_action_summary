<template>
  <div class="login-container">
    <div class="login-card success-card">
      <div class="success-icon">&#10003;</div>
      <h1>提交成功！</h1>
      <p>{{ store.name }} 同学，你的学习单已经提交完成。</p>
      <button @click="switchUser" class="btn-primary">切换用户</button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'

const router = useRouter()
const store = useStudentStore()

function switchUser() {
  store.reset()
  router.push('/')
}
</script>
