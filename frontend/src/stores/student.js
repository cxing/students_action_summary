import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'

export const useStudentStore = defineStore('student', () => {
  const studentId = ref(null)
  const name = ref('')
  const levels = reactive({
    1: { answer: null, stars: 0, attempts: 0 },
    2: { answer: null, stars: 0, attempts: 0 },
    3: { answer: null, stars: 0, attempts: 0 },
    4: { answer: null, stars: 0, attempts: 0 },
    5: { answer: null, stars: 0, attempts: 0 },
  })

  const totalStars = computed(() => {
    return Object.values(levels).reduce((sum, l) => sum + l.stars, 0)
  })

  function setStudent(id, studentName) { studentId.value = id; name.value = studentName }

  function setLevel(levelNo, data) {
    Object.assign(levels[levelNo], data)
  }

  function restoreLevels(existingLevels) {
    for (const [lvl, data] of Object.entries(existingLevels)) {
      const lv = parseInt(lvl)
      if (lv >= 1 && lv <= 5) {
        levels[lv].stars = data.stars || 0
        levels[lv].attempts = data.attempts || 0
        levels[lv].answer = data.answer || null
      }
    }
  }

  function reset() {
    studentId.value = null
    name.value = ''
    for (let i = 1; i <= 5; i++) {
      levels[i] = { answer: null, stars: 0, attempts: 0 }
    }
  }

  return { studentId, name, levels, totalStars, setStudent, setLevel, restoreLevels, reset }
})
