import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? ''
const AUTH_KEY = 'cinestream_auth'

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

let onUnauthorized = () => {}

export function setUnauthorizedHandler(fn) {
  onUnauthorized = typeof fn === 'function' ? fn : () => {}
}

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      clearAuth()
      onUnauthorized()
    }
    return Promise.reject(err)
  },
)

export function getAuth() {
  try {
    const raw = localStorage.getItem(AUTH_KEY)
    if (!raw) return null
    const data = JSON.parse(raw)
    if (data?.access_token && data?.user?.user_id != null && data?.user?.username) {
      return data
    }
  } catch {
    /* ignore */
  }
  return null
}

export function setAuth(payload) {
  if (!payload?.access_token || !payload?.user) {
    clearAuth()
    return
  }
  localStorage.setItem(
    AUTH_KEY,
    JSON.stringify({
      access_token: payload.access_token,
      token_type: payload.token_type || 'bearer',
      user: {
        user_id: payload.user.user_id,
        username: payload.user.username,
        email: payload.user.email,
      },
    }),
  )
}

export function clearAuth() {
  localStorage.removeItem(AUTH_KEY)
}

export function getAccessToken() {
  return getAuth()?.access_token ?? null
}

export function getStoredUser() {
  return getAuth()?.user ?? null
}
