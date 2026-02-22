<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, setAuth } from '../api/client'

const router = useRouter()
const route = useRoute()

const mode = ref('signin')
const username = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function signIn() {
  error.value = ''
  if (!username.value.trim() || !password.value) {
    error.value = 'Enter username and password.'
    return
  }
  loading.value = true
  try {
    const { data } = await api.post('/api/v1/auth/login', {
      username: username.value.trim(),
      password: password.value,
    })
    setAuth(data)
    const redirect = route.query.redirect || '/'
    router.push(typeof redirect === 'string' ? redirect : '/')
  } catch (e) {
    const d = e.response?.data?.detail
    error.value =
      typeof d === 'string' ? d : d ? JSON.stringify(d) : e.message || 'Sign in failed.'
  } finally {
    loading.value = false
  }
}

async function register() {
  error.value = ''
  if (!username.value.trim() || !email.value.trim() || !password.value) {
    error.value = 'Username, email, and password are required.'
    return
  }
  if (password.value.length < 8) {
    error.value = 'Password must be at least 8 characters.'
    return
  }
  loading.value = true
  try {
    const { data } = await api.post('/api/v1/auth/register', {
      username: username.value.trim(),
      email: email.value.trim(),
      password: password.value,
    })
    setAuth(data)
    router.push('/')
  } catch (e) {
    const d = e.response?.data?.detail
    error.value =
      typeof d === 'string' ? d : d ? JSON.stringify(d) : e.message || 'Registration failed.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <h1>Join the community</h1>
    <p class="lead muted">
      Sign in with your username and password, or create an account. JWT is stored in the browser for
      this demo — use a strong <code>JWT_SECRET_KEY</code> in production.
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
      <label class="field">
        <span>Password</span>
        <input
          v-model="password"
          type="password"
          :autocomplete="mode === 'signin' ? 'current-password' : 'new-password'"
          placeholder="••••••••"
        />
      </label>
      <p v-if="mode === 'register'" class="muted tiny">Minimum 8 characters for new passwords.</p>
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
.lead code {
  font-size: 0.85em;
  padding: 0.15em 0.35em;
  border-radius: 6px;
  background: var(--surface2);
  border: 1px solid var(--border);
}
.lead {
  max-width: 38rem;
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
.tiny {
  font-size: 0.8rem;
  margin: -0.5rem 0 0;
}
.submit {
  margin-top: 0.25rem;
}
</style>
