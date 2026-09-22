import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '../api/client'
import { connectSocket, disconnectSocket } from '../api/socket'

const STORAGE_KEY = 'ticket_triage_token'

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return typeof payload.exp !== 'number' || payload.exp * 1000 < Date.now()
  } catch {
    return true
  }
}

export const useAuthStore = defineStore('auth', () => {
  const stored = localStorage.getItem(STORAGE_KEY)
  const token = ref<string | null>(stored && !isTokenExpired(stored) ? stored : null)
  if (stored && !token.value) localStorage.removeItem(STORAGE_KEY)

  const isAuthenticated = computed(() => token.value !== null)

  async function login(username: string, password: string) {
    const { token: newToken } = await api.login(username, password)
    token.value = newToken
    localStorage.setItem(STORAGE_KEY, newToken)
    connectSocket(newToken)
  }

  function logout() {
    token.value = null
    localStorage.removeItem(STORAGE_KEY)
    disconnectSocket()
  }

  return { token, isAuthenticated, login, logout }
})
