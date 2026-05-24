import axios from 'axios'

const api = axios.create({ baseURL: '/api', withCredentials: true })

export function studentLogin(name) { return api.post('/student/login', { name }) }
export function teacherLogin(username, password) { return api.post('/teacher/login', { username, password }) }
export function teacherCheck() { return api.get('/teacher/check') }

export function submitAll(studentId, answers, drawingPoints, selfCheck) {
  return api.post('/submit', {
    student_id: studentId,
    answers: Object.entries(answers).map(([qno, ans]) => ({ question_no: parseInt(qno), answer: ans })),
    drawing_points: drawingPoints,
    self_check: {
      point_check: selfCheck.pointCheck || '',
      line_check: selfCheck.lineCheck || '',
      draw_check: selfCheck.drawCheck || '',
      note: selfCheck.note || '',
    },
  })
}

export function getDashboard() { return api.get('/teacher/dashboard') }
export function getStudentDetail(studentId) { return api.get(`/teacher/student/${studentId}`) }
