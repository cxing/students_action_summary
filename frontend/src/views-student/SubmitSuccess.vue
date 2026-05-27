<template>
  <div class="login-container">
    <div class="login-card success-card">
      <div class="success-icon">&#9733;</div>
      <h1>闯关完成!</h1>
      <p>{{ store.name }} 同学，你一共获得了 <strong>{{ store.totalStars }} / 15</strong> 颗星</p>

      <div class="stars-breakdown">
        <div v-for="lv in 5" :key="lv" class="star-row">
          <span class="star-level">第{{ lv }}关</span>
          <span class="star-count">
            <template v-for="s in 3" :key="s">
              <span :class="s <= store.levels[lv].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
            </template>
          </span>
        </div>
      </div>

      <button @click="switchUser" class="btn-primary" style="margin-top: 20px;">切换用户</button>
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
