import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'StudentLogin', component: () => import('../views-student/StudentLogin.vue') },
  { path: '/level/1', name: 'Level1', component: () => import('../views-student/Level1Balloon.vue') },
  { path: '/level/2', name: 'Level2', component: () => import('../views-student/Level2DragDrop.vue') },
  { path: '/level/3', name: 'Level3', component: () => import('../views-student/Level3CarRide.vue') },
  { path: '/level/4', name: 'Level4', component: () => import('../views-student/Level4WaterTank.vue') },
  { path: '/level/5', name: 'Level5', component: () => import('../views-student/Level5Thermometer.vue') },
  { path: '/submit-success', name: 'SubmitSuccess', component: () => import('../views-student/SubmitSuccess.vue') },
  { path: '/teacher', name: 'TeacherLogin', component: () => import('../views-teacher/TeacherLogin.vue') },
  { path: '/teacher/dashboard', name: 'Dashboard', component: () => import('../views-teacher/Dashboard.vue') },
  { path: '/teacher/student/:id', name: 'StudentDetail', component: () => import('../views-teacher/StudentDetail.vue'), props: true },
]

const router = createRouter({ history: createWebHistory(), routes })
export default router
