import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export const useStudentStore = defineStore('student', () => {
  const studentId = ref(null)
  const name = ref('')
  const answers = ref({})
  const drawingPoints = ref([])
  const selfCheck = reactive({ pointCheck: '', lineCheck: '', drawCheck: '', note: '' })

  function setStudent(id, studentName) { studentId.value = id; name.value = studentName }
  function setAnswer(questionNo, answer) {
    answers.value = { ...answers.value, [questionNo]: answer }
  }
  function setDrawing(points) { drawingPoints.value = points }
  function setSelfCheck(check) {
    selfCheck.pointCheck = check.pointCheck || ''
    selfCheck.lineCheck = check.lineCheck || ''
    selfCheck.drawCheck = check.drawCheck || ''
    selfCheck.note = check.note || ''
  }
  function reset() {
    studentId.value = null; name.value = ''
    answers.value = {}
    drawingPoints.value = []
    selfCheck.pointCheck = ''; selfCheck.lineCheck = ''; selfCheck.drawCheck = ''; selfCheck.note = ''
  }
  return { studentId, name, answers, drawingPoints, selfCheck, setStudent, setAnswer, setDrawing, setSelfCheck, reset }
})
