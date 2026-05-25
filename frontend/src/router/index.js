import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'StudentLogin', component: () => import('../views-student/StudentLogin.vue') },
  { path: '/preview', name: 'DataPreview', component: () => import('../views-student/DataPreview.vue') },
  { path: '/questions', name: 'ChoiceQuestions', component: () => import('../views-student/ChoiceQuestions.vue') },
  { path: '/fill-blank', name: 'FillBlankQuestion', component: () => import('../views-student/FillBlankQuestion.vue') },
  { path: '/drawing', name: 'DrawingQuestion', component: () => import('../views-student/DrawingQuestion.vue') },
  { path: '/self-check', name: 'SelfCheck', component: () => import('../views-student/SelfCheck.vue') },
  { path: '/submit-success', name: 'SubmitSuccess', component: () => import('../views-student/SubmitSuccess.vue') },
  { path: '/teacher', name: 'TeacherLogin', component: () => import('../views-teacher/TeacherLogin.vue') },
  { path: '/teacher/dashboard', name: 'Dashboard', component: () => import('../views-teacher/Dashboard.vue') },
  { path: '/teacher/student/:id', name: 'StudentDetail', component: () => import('../views-teacher/StudentDetail.vue'), props: true },
]

const router = createRouter({ history: createWebHistory(), routes })
export default router
