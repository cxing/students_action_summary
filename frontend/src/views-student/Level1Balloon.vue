<template>
  <div class="level-container">
    <div class="level-header">
      <span class="level-badge">第 1 关</span>
      <span class="level-title">🎈 射击气球</span>
      <div class="star-display">
        <span v-for="s in 3" :key="s" :class="s <= store.levels[1].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
      </div>
    </div>

    <div class="game-card">
      <p class="question-text">折线统计图中的"点"和"线"分别表示什么？</p>
      <p class="subtitle">点击正确的一组气球，用飞镖射中它！</p>

      <div class="balloon-field">
        <div
          v-for="opt in options"
          :key="opt.key"
          class="balloon-pair"
          :class="{ 'balloon-hit': hitKey === opt.key, 'balloon-shake': shakeKey === opt.key }"
        >
          <div class="balloon balloon-point" @click="shoot(opt)">
            <div class="balloon-string"></div>
            <div class="balloon-body" :style="{ background: opt.color }">
              <span class="balloon-label">点</span>
              <span class="balloon-text">{{ opt.point }}</span>
            </div>
          </div>
          <div class="balloon balloon-line" @click="shoot(opt)">
            <div class="balloon-string"></div>
            <div class="balloon-body" :style="{ background: opt.color }">
              <span class="balloon-label">线</span>
              <span class="balloon-text">{{ opt.line }}</span>
            </div>
          </div>
          <span class="pair-letter">{{ opt.key }}</span>
        </div>
      </div>

      <div v-if="result !== null" :class="result ? 'feedback-correct' : 'feedback-wrong'">
        {{ result ? '🎯 射中了！太棒了！点表示数量的多少，线表示数量的变化趋势。' : '💨 没射中，再试一次！' }}
      </div>

      <div class="nav-buttons">
        <router-link to="/" class="btn-secondary">退出</router-link>
        <router-link to="/level/2" class="btn-primary">下一关 →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useStudentStore } from '../stores/student.js'
import { submitLevel } from '../api.js'

const store = useStudentStore()
const result = ref(null)
const hitKey = ref(null)
const shakeKey = ref(null)

const options = [
  { key: 'A', point: '数量的多少', line: '数量的变化趋势', color: '#e74c3c', correct: true },
  { key: 'B', point: '图形的颜色', line: '数量的单位', color: '#3498db', correct: false },
  { key: 'C', point: '统计图的标题', line: '横轴的长度', color: '#2ecc71', correct: false },
]

async function shoot(opt) {
  if (hitKey.value) return
  const isCorrect = opt.correct
  const attempts = store.levels[1].attempts + 1
  const stars = isCorrect
    ? (attempts === 1 ? 3 : attempts === 2 ? 2 : 1)
    : 0

  hitKey.value = opt.key
  if (!isCorrect) {
    shakeKey.value = opt.key
    setTimeout(() => { shakeKey.value = null; hitKey.value = null }, 600)
  }

  store.setLevel(1, { answer: opt.key, stars: isCorrect ? stars : 0, attempts })
  result.value = isCorrect

  try {
    await submitLevel(store.studentId, 1, opt.key, isCorrect ? stars : 0, attempts)
  } catch (e) {
    // game continues even if submit fails
  }
}
</script>
