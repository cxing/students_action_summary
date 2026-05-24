import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTeacherStore = defineStore('teacher', () => {
  const loggedIn = ref(false)
  function setLoggedIn(val) { loggedIn.value = val }
  return { loggedIn, setLoggedIn }
})
