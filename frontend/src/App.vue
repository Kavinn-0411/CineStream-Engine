<script setup>
import { computed } from 'vue'
import { useRoute, useRouter, RouterLink, RouterView } from 'vue-router'
import { getStoredUser, setStoredUser } from './api/client'

const route = useRoute()
const router = useRouter()
const user = computed(() => getStoredUser())

function logout() {
  setStoredUser(null)
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="layout">
    <header class="header">
      <div class="header-inner">
        <RouterLink to="/" class="brand">
          <span class="brand-mark">▶</span>
          CineStream
        </RouterLink>
        <nav class="nav">
          <RouterLink to="/">Home</RouterLink>
          <RouterLink v-if="user" to="/dashboard">Search & review</RouterLink>
          <RouterLink v-if="!user" to="/login">Sign in</RouterLink>
          <template v-else>
            <span class="user-pill">{{ user.username }}</span>
            <button type="button" class="btn btn-ghost" @click="logout">Sign out</button>
          </template>
        </nav>
      </div>
    </header>

    <main class="main">
      <RouterView :key="route.path" />
    </main>

    <footer class="footer">
      <p class="muted">CineStream Engine — reviews → Kafka → Spark → recommendations</p>
    </footer>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.header {
  border-bottom: 1px solid var(--border);
  background: rgba(12, 15, 20, 0.85);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-inner {
  max-width: 960px;
  margin: 0 auto;
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.brand {
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.brand:hover {
  text-decoration: none;
  color: var(--accent);
}
.brand-mark {
  color: var(--accent);
  font-size: 1rem;
}
.nav {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}
.nav a {
  font-weight: 600;
  color: var(--muted);
}
.nav a.router-link-active {
  color: var(--accent);
}
.user-pill {
  font-size: 0.85rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text);
}
.btn-ghost {
  padding: 0.4rem 0.75rem;
  font-size: 0.85rem;
  background: transparent;
}
.main {
  flex: 1;
  max-width: 960px;
  width: 100%;
  margin: 0 auto;
  padding: 2rem 1.25rem 3rem;
}
.footer {
  border-top: 1px solid var(--border);
  padding: 1rem 1.25rem;
  text-align: center;
}
.footer p {
  margin: 0;
}
</style>
