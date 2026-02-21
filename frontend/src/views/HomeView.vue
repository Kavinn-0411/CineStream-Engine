<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api, getStoredUser } from '../api/client'

const user = ref(getStoredUser())
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
    const { data } = await api.get(`/api/v1/recommendations/${user.value.user_id}`, {
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

onMounted(() => {
  user.value = getStoredUser()
  loadRecommendations()
})
</script>

<template>
  <div class="page">
    <h1>Welcome{{ user ? `, ${user.username}` : '' }}</h1>

    <template v-if="!user">
      <p class="welcome muted">
        Welcome to the <strong>Movie Buff</strong> community. Share your views on the movies you’ve
        watched — sign in to get a personal dashboard and, once the pipeline has processed your
        reviews, tailored picks on this home page.
      </p>
      <RouterLink to="/login" class="btn btn-primary">Sign in or register</RouterLink>
    </template>

    <template v-else>
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
          you’ve watched — head to your dashboard to search a title and leave a review. When the
          streaming job runs, personalized recommendations can appear here.
        </p>
        <RouterLink to="/dashboard" class="btn btn-primary">Search &amp; write a review</RouterLink>
      </section>
    </template>
  </div>
</template>

<style scoped>
.page h1 {
  font-family: var(--font-display);
  font-size: 2.25rem;
  margin: 0 0 1rem;
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
.small {
  font-size: 0.875rem;
  margin: 0 0 1.25rem;
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
.score {
  margin: 0.75rem 0 0;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--accent-dim);
}
</style>
