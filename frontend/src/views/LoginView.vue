<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '../api/client'
import { useAuthStore } from '../stores/auth'

const username = ref('')
const password = ref('')
const error = ref<string | null>(null)
const submitting = ref(false)

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

async function handleSubmit() {
  error.value = null
  submitting.value = true
  try {
    await auth.login(username.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.push(redirect)
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Unable to log in'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <form class="login-card" @submit.prevent="handleSubmit">
      <h1>Ticket Triage</h1>
      <p class="subtitle">Sign in to view incoming tickets</p>

      <label for="username">Username</label>
      <input id="username" v-model="username" type="text" autocomplete="username" required />

      <label for="password">Password</label>
      <input id="password" v-model="password" type="password" autocomplete="current-password" required />

      <p v-if="error" class="error">{{ error }}</p>

      <button type="submit" class="submit" :disabled="submitting">
        {{ submitting ? 'Signing in…' : 'Sign in' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 320px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

h1 {
  margin: 0;
  font-size: 1.4rem;
}

.subtitle {
  margin: 0 0 1rem;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

label {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-top: 0.5rem;
}

input {
  padding: 0.5rem 0.6rem;
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

.error {
  color: var(--color-danger);
  font-size: 0.85rem;
  margin: 0.5rem 0 0;
}

.submit {
  margin-top: 1.25rem;
  padding: 0.6rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
}

.submit:hover:not(:disabled) {
  background: var(--color-primary-hover);
}
</style>
