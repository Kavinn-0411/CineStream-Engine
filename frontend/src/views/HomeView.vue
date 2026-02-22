<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { api, getStoredUser, clearAuth } from '../api/client'
import DashboardView from './DashboardView.vue'

const router = useRouter()

/** Always read fresh auth from localStorage (fixes stale state after login). */
const user = computed(() => getStoredUser())

const activeTab = ref('recs')
const loading = ref(false)
const error = ref('')
const items = ref([])
const total = ref(0)

async function loadRecommendations() {
  if (!user.value?.user_id) {
    items.value = []
    total.value = 0
    return
  }
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/api/v1/me/recommendations', {
      params: { limit: 12 },
    })
    items.value = data.items || []
    total.value = data.total ?? 0
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Could not load recommendations.'
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

watch(
  () => user.value?.user_id,
  (id) => {
    if (id) {
      loadRecommendations()
    } else {
      items.value = []
      total.value = 0
      activeTab.value = 'recs'
    }
  },
  { immediate: true },
)

function logout() {
  clearAuth()
  activeTab.value = 'recs'
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>Welcome{{ user ? `, ${user.username}` : '' }}</h1>
      <div v-if="user" class="home-toolbar">
        <button type="button" class="btn btn-ghost" @click="logout">Sign out</button>
      </div>
    </div>

    <template v-if="!user">
      <p class="welcome muted">
        Welcome to the <strong>Movie Buff</strong> community. Share your views on the movies you’ve
        watched — sign in to get a personal dashboard and, once the pipeline has processed your
        reviews, tailored picks on this home page.
      </p>
      <RouterLink to="/login" class="btn btn-primary">Sign in or register</RouterLink>
    </template>

    <template v-else>
      <div class="tabs" role="tablist" aria-label="Home sections">
        <button
          type="button"
          role="tab"
          :aria-selected="activeTab === 'recs'"
          :class="['tab', { active: activeTab === 'recs' }]"
          @click="activeTab = 'recs'"
        >
          For you
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="activeTab === 'review'"
          :class="['tab', { active: activeTab === 'review' }]"
          @click="activeTab = 'review'"
        >
          Write a review
        </button>
        <RouterLink to="/dashboard" class="tab-link">Open full dashboard →</RouterLink>
      </div>

      <div v-show="activeTab === 'recs'" class="tab-panel">
        <p v-if="loading" class="muted">Loading recommendations…</p>
        <p v-else-if="error" class="error-msg">{{ error }}</p>

        <section v-else-if="items.length > 0" class="recs">
          <h2>Recommended for you</h2>
          <ul class="grid">
            <li v-for="m in items" :key="m.movie_id" class="card movie-card">
              <h3>{{ m.title }}</h3>
              <p class="muted meta">
                <span v-if="m.imdb_rating != null">IMDb {{ m.imdb_rating }}</span>
                <span v-if="m.genres">{{ m.genres }}</span>
              </p>
            </li>
          </ul>
        </section>

        <section v-else class="welcome-block card">
          <p class="welcome">
            Welcome to the <strong>Movie Buff</strong> community. Share your views on the movies
            you’ve watched — use the <strong>Write a review</strong> tab or the full dashboard. When
            the streaming job runs, personalized recommendations can appear here.
          </p>
        </section>
      </div>

      <div v-show="activeTab === 'review'" class="tab-panel review-panel">
        <DashboardView embedded @review-submitted="loadRecommendations" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}
.home-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.page h1 {
  font-family: var(--font-display);
  font-size: 2.25rem;
  margin: 0;
}
.tabs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin: 1rem 0 1.25rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.75rem;
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
.tab-link {
  margin-left: auto;
  font-size: 0.9rem;
  font-weight: 600;
}
.tab-panel {
  min-height: 2rem;
}
.review-panel {
  margin-top: 0.25rem;
}
.welcome {
  font-size: 1.05rem;
  max-width: 40rem;
  margin: 0 0 1.25rem;
  line-height: 1.6;
}
.welcome strong {
  color: var(--accent);
}
.welcome-block {
  max-width: 40rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: flex-start;
}
.recs h2 {
  font-size: 1.35rem;
  margin: 0 0 0.25rem;
}
.grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
}
.movie-card h3 {
  margin: 0 0 0.5rem;
  font-size: 1.05rem;
  line-height: 1.3;
}
.meta {
  font-size: 0.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
</style>
