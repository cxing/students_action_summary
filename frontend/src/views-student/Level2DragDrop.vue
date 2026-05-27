<template>
  <div class="level-container">
    <div class="level-header">
      <span class="level-badge">第 2 关</span>
      <span class="level-title">🧩 拖拽分类</span>
      <div class="star-display">
        <span v-for="s in 3" :key="s" :class="s <= store.levels[2].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
      </div>
    </div>

    <div class="game-card">
      <details class="ref-tables" open>
        <summary>统计数据参考（点击收起/展开）</summary>
        <div class="table-section">
          <h4>统计表一：6名同学一分钟仰卧起坐个数统计表</h4>
          <table class="data-table">
            <thead><tr><th>姓名</th><th>周子昂</th><th>许明哲</th><th>沈嘉诚</th><th>叶思涵</th><th>李欣怡</th><th>吴俊杰</th></tr></thead>
            <tbody><tr><td>个数/个</td><td>35</td><td>42</td><td>38</td><td>40</td><td>36</td><td>33</td></tr></tbody>
          </table>
        </div>
        <div class="table-section">
          <h4>统计表二：许明哲连续6天一分钟仰卧起坐成绩统计表</h4>
          <table class="data-table">
            <thead><tr><th>日期</th><th>周一</th><th>周二</th><th>周三</th><th>周四</th><th>周五</th><th>周六</th></tr></thead>
            <tbody><tr><td>个数/个</td><td>30</td><td>32</td><td>35</td><td>36</td><td>39</td><td>42</td></tr></tbody>
          </table>
        </div>
      </details>

      <p class="question-text">分别将两个统计表场景拖入正确的统计图篮子里：</p>

      <div class="drag-cards">
        <div
          v-for="card in cards"
          :key="card.id"
          class="drag-card"
          :class="cardClasses(card)"
          :draggable="!card.placed"
          @dragstart="onDragStart($event, card)"
          @dragend="onDragEnd"
        >
          {{ card.label }}
        </div>
      </div>

      <div class="drop-zones">
        <div
          class="drop-zone"
          :class="{ 'zone-hover': hoverZone === 'bar', 'zone-filled': zoneBar }"
          @dragover.prevent="hoverZone = 'bar'"
          @dragleave="hoverZone = null"
          @drop="onDrop($event, 'bar')"
        >
          <div class="zone-icon">📊</div>
          <div class="zone-label">条形统计图</div>
          <div class="zone-hint">用于比较数量的多少</div>
          <div v-if="zoneBar" class="zone-result" :class="zoneBar.correct ? 'correct' : 'wrong'">
            {{ zoneBar.correct ? '✓' : '✗' }} {{ zoneBar.label }}
          </div>
        </div>
        <div
          class="drop-zone"
          :class="{ 'zone-hover': hoverZone === 'line', 'zone-filled': zoneLine }"
          @dragover.prevent="hoverZone = 'line'"
          @dragleave="hoverZone = null"
          @drop="onDrop($event, 'line')"
        >
          <div class="zone-icon">📈</div>
          <div class="zone-label">折线统计图</div>
          <div class="zone-hint">用于表示数量的变化趋势</div>
          <div v-if="zoneLine" class="zone-result" :class="zoneLine.correct ? 'correct' : 'wrong'">
            {{ zoneLine.correct ? '✓' : '✗' }} {{ zoneLine.label }}
          </div>
        </div>
      </div>

      <div v-if="allPlaced" :class="allCorrect ? 'feedback-correct' : 'feedback-wrong'">
        <template v-if="allCorrect">🎉 全部分类正确！比较数量的多少用条形统计图，表示数量变化趋势用折线统计图。</template>
        <template v-else>还有分类不对哦，点击卡片可以重新拖拽&nbsp;
          <button @click="resetAll" class="btn-small">重试</button>
        </template>
      </div>

      <div class="nav-buttons">
        <router-link to="/level/1" class="btn-secondary">上一关</router-link>
        <router-link to="/level/3" class="btn-primary">下一关 →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStudentStore } from '../stores/student.js'
import { submitLevel } from '../api.js'

const store = useStudentStore()
const hoverZone = ref(null)
const dragCard = ref(null)
const zoneBar = ref(null)
const zoneLine = ref(null)

const cards = ref([
  { id: 'table1', label: '统计表一场景\n（比较6名同学个数多少）', placed: false, correct: null, targetZone: 'bar' },
  { id: 'table2', label: '统计表二场景\n（表示许明哲6天成绩变化）', placed: false, correct: null, targetZone: 'line' },
])

const allPlaced = computed(() => cards.value.every(c => c.placed))
const allCorrect = computed(() => cards.value.every(c => c.correct === true))

function cardClasses(card) {
  return {
    'card-placed': card.placed,
    'card-correct': card.placed && card.correct,
    'card-wrong': card.placed && !card.correct,
  }
}

function onDragStart(e, card) {
  if (card.placed) { e.preventDefault(); return }
  dragCard.value = card
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', card.id)
}

function onDragEnd() {
  hoverZone.value = null
  dragCard.value = null
}

function onDrop(e, zone) {
  hoverZone.value = null
  if (!dragCard.value) return
  const card = cards.value.find(c => c.id === dragCard.value.id)
  if (!card || card.placed) return

  const isCorrect = card.targetZone === zone
  card.placed = true
  card.correct = isCorrect

  const cardLabel = card.label.split('\n')[0]
  if (zone === 'bar') zoneBar.value = { label: cardLabel, correct: isCorrect }
  if (zone === 'line') zoneLine.value = { label: cardLabel, correct: isCorrect }

  if (allPlaced.value) submitResult()
}

function resetAll() {
  cards.value.forEach(c => { c.placed = false; c.correct = null })
  zoneBar.value = null
  zoneLine.value = null
}

async function submitResult() {
  const answer = {}
  cards.value.forEach(c => {
    const subNo = c.id === 'table1' ? '1' : '2'
    answer[subNo] = c.correct ? (c.targetZone === 'bar' ? 'A' : 'B') : 'X'
  })
  const attempts = store.levels[2].attempts + 1
  const stars = allCorrect.value ? (attempts === 1 ? 3 : attempts === 2 ? 2 : 1) : 0
  store.setLevel(2, { answer, stars, attempts })
  try {
    await submitLevel(store.studentId, 2, answer, stars, attempts)
  } catch (e) { /* continue */ }
}
</script>
