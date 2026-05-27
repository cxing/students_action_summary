import axios from 'axios'

const api = axios.create({ baseURL: '/api', withCredentials: true })

export function studentLogin(name) { return api.post('/student/login', { name }) }
export function teacherLogin(username, password) { return api.post('/teacher/login', { username, password }) }
export function teacherCheck() { return api.get('/teacher/check') }

export function submitLevel(studentId, levelNo, answer, stars, attempts) {
  return api.post('/level/submit', {
    student_id: studentId,
    level_no: levelNo,
    answer: answer,
    stars: stars,
    attempts: attempts,
  })
}

export function getDashboard() { return api.get('/teacher/dashboard') }
export function getStudentDetail(studentId) { return api.get(`/teacher/student/${studentId}`) }
export function deleteStudentSubmission(studentId) { return api.delete(`/teacher/student/${studentId}`) }
export function getChartUrl(type) { return `/api/teacher/chart?type=${type}` }
