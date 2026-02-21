import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? ''

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

export function getStoredUser() {
  try {
    const raw = localStorage.getItem('cinestream_user')
    if (!raw) return null
    const u = JSON.parse(raw)
    if (u?.user_id && u?.username) return u
  } catch {
    /* ignore */
  }
  return null
}

export function setStoredUser(user) {
  if (!user) {
    localStorage.removeItem('cinestream_user')
    return
  }
  localStorage.setItem(
    'cinestream_user',
    JSON.stringify({
      user_id: user.user_id,
      username: user.username,
      email: user.email,
    }),
  )
}
