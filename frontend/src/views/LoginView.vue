<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, setStoredUser } from '../api/client'

const router = useRouter()
const route = useRoute()

const mode = ref('signin')
const username = ref('')
const email = ref('')
const loading = ref(false)
const error = ref('')

async function signIn() {
  error.value = ''
  if (!username.value.trim()) {
    error.value = 'Enter your username.'
    return
  }
  loading.value = true
  try {
    const { data } = await api.get(
      `/api/v1/users/by-username/${encodeURIComponent(username.value.trim())}`,
    )
    setStoredUser(data)
    const redirect = route.query.redirect || '/'
    router.push(typeof redirect === 'string' ? redirect : '/')
  } catch (e) {
    if (e.response?.status === 404) {
      error.value = 'No account with that username. Register below.'
    } else {
      error.value = e.response?.data?.detail || e.message || 'Sign in failed.'
    }
  } finally {
    loading.value = false
  }
}

async function register() {
  error.value = ''
  if (!username.value.trim() || !email.value.trim()) {
    error.value = 'Username and email are required.'
    return
  }
  loading.value = true
  try {
    const { data } = await api.post('/api/v1/users', {
      username: username.value.trim(),
      email: email.value.trim(),
    })
    setStoredUser(data)
    router.push('/')
  } catch (e) {
    error.value =
      e.response?.data?.detail ||
      (typeof e.response?.data?.detail === 'object'
        ? JSON.stringify(e.response.data.detail)
        : null) ||
      e.message ||
      'Registration failed.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <h1>Join the community</h1>
    <p class="lead muted">
      Create an account or sign in with your username. Your dashboard is where you search films and
      post reviews — recommendations on the home page update after the streaming pipeline runs.
    </p>

    <div class="tabs">
      <button
        type="button"
        :class="['tab', { active: mode === 'signin' }]"
        @click="mode = 'signin'"
      >
        Sign in
      </button>
      <button
        type="button"
        :class="['tab', { active: mode === 'register' }]"
        @click="mode = 'register'"
      >
        Register
      </button>
    </div>

    <div class="card form-card">
      <label class="field">
        <span>Username</span>
        <input v-model="username" autocomplete="username" placeholder="moviebuff42" />
      </label>
      <label v-if="mode === 'register'" class="field">
        <span>Email</span>
        <input
          v-model="email"
          type="email"
          autocomplete="email"
          placeholder="you@example.com"
        />
      </label>
      <p v-if="error" class="error-msg">{{ error }}</p>
      <button
        type="button"
        class="btn btn-primary submit"
        :disabled="loading"
        @click="mode === 'signin' ? signIn() : register()"
      >
        {{ loading ? 'Please wait…' : mode === 'signin' ? 'Sign in' : 'Create account' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.page h1 {
  font-family: var(--font-display);
  font-size: 2rem;
  margin: 0 0 0.5rem;
}
.lead {
  max-width: 36rem;
  margin-bottom: 1.5rem;
}
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.tab {
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--surface2);
  color: var(--muted);
  font-family: inherit;
  font-weight: 600;
  cursor: pointer;
}
.tab.active {
  color: var(--text);
  border-color: var(--accent-dim);
  background: var(--surface);
}
.form-card {
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.field span {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--muted);
}
.submit {
  margin-top: 0.25rem;
}
</style>
