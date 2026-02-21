<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { api, getStoredUser } from '../api/client'

/** Minimum characters before we hit the movies API (avoids huge result sets on 1 letter). */
const MIN_QUERY_LEN = 2
const DEBOUNCE_MS = 320

const user = ref(getStoredUser())
const search = ref('')
const searching = ref(false)
const movies = ref([])
const searchError = ref('')

const selectedMovie = ref(null)
const reviewText = ref('')
const submitting = ref(false)
const submitMessage = ref('')
const submitError = ref('')

let debounceTimer = null
let abortController = null

const canSubmit = computed(
  () =>
    selectedMovie.value &&
    reviewText.value.trim().length >= 3 &&
    user.value?.user_id &&
    !submitting.value,
)

function clearResults() {
  movies.value = []
  searchError.value = ''
  selectedMovie.value = null
}

async function fetchMoviesForQuery(q) {
  const query = q.trim()
  if (query.length < MIN_QUERY_LEN) {
    clearResults()
    return
  }

  if (abortController) {
    abortController.abort()
  }
  abortController = new AbortController()

  searching.value = true
  searchError.value = ''
  try {
    const { data } = await api.get('/api/v1/movies', {
      params: { search: query, page: 1, size: 30 },
      signal: abortController.signal,
    })
    movies.value = data.items || []
    if (!movies.value.length) {
      searchError.value = 'No movies matched. Keep typing or try other words.'
    } else {
      // Drop selection if the movie is no longer in this result set
      if (
        selectedMovie.value &&
        !movies.value.some((m) => m.movie_id === selectedMovie.value.movie_id)
      ) {
        selectedMovie.value = null
      }
    }
  } catch (e) {
    if (e.code === 'ERR_CANCELED' || e.name === 'CanceledError' || e.name === 'AbortError') {
      return
    }
    movies.value = []
    searchError.value = e.response?.data?.detail || e.message || 'Search failed.'
  } finally {
    searching.value = false
  }
}

watch(search, (q) => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = setTimeout(() => {
    debounceTimer = null
    fetchMoviesForQuery(q)
  }, DEBOUNCE_MS)
})

function pickMovie(m) {
  selectedMovie.value = m
  submitMessage.value = ''
  submitError.value = ''
}

async function submitReview() {
  if (!canSubmit.value) return
  submitting.value = true
  submitMessage.value = ''
  submitError.value = ''
  try {
    await api.post('/api/v1/reviews', {
      user_id: user.value.user_id,
      movie_id: selectedMovie.value.movie_id,
      review_text: reviewText.value.trim(),
    })
    submitMessage.value =
      'Review sent to Kafka. Preferences & recommendations update on the next Spark micro-batch.'
    reviewText.value = ''
    selectedMovie.value = null
  } catch (e) {
    const d = e.response?.data?.detail
    submitError.value = typeof d === 'string' ? d : JSON.stringify(d) || e.message || 'Failed.'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  user.value = getStoredUser()
})

onUnmounted(() => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  if (abortController) {
    abortController.abort()
  }
})
</script>

<template>
  <div class="page">
    <h1>Movie search &amp; review</h1>
    <p class="muted intro" v-if="user">
      Signed in as <strong>{{ user.username }}</strong>. Type in the box matching movies appear as
      you type. Pick one, write your review, then submit.
    </p>

    <section class="card section">
      <h2>Find a movie</h2>
      <p class="hint muted">
        Type at least <strong>{{ MIN_QUERY_LEN }}</strong> letters; results update automatically.
      </p>
      <div class="search-wrap">
        <input
          v-model="search"
          type="search"
          autocomplete="off"
          placeholder="Start typing a movie title…"
          aria-label="Search movies by title"
          aria-describedby="search-hint"
        />
        <span v-if="searching" class="search-status" aria-live="polite">Searching…</span>
      </div>
      <p id="search-hint" class="sr-only">
        Results load as you type after a short pause. Select a film to write a review.
      </p>
      <p v-if="searchError" class="error-msg">{{ searchError }}</p>
      <p
        v-else-if="search.trim().length > 0 && search.trim().length < MIN_QUERY_LEN"
        class="muted tiny"
      >
        Enter {{ MIN_QUERY_LEN - search.trim().length }} more character(s) to search.
      </p>

      <ul v-if="movies.length" class="results" role="listbox" aria-label="Movie matches">
        <li v-for="m in movies" :key="m.movie_id" role="option">
          <button
            type="button"
            class="movie-row"
            :class="{ active: selectedMovie?.movie_id === m.movie_id }"
            @click="pickMovie(m)"
          >
            <span class="title">{{ m.title }}</span>
            <span class="muted small">{{ m.genres || '—' }} · IMDb {{ m.imdb_rating ?? '—' }}</span>
          </button>
        </li>
      </ul>
    </section>

    <section class="card section" v-if="selectedMovie">
      <h2>Your review — {{ selectedMovie.title }}</h2>
      <textarea
        v-model="reviewText"
        rows="6"
        placeholder="What did you think? (min 3 characters)"
        aria-label="Review text"
      />
      <button type="button" class="btn btn-primary" :disabled="!canSubmit" @click="submitReview">
        {{ submitting ? 'Submitting…' : 'Submit review to API' }}
      </button>
      <p v-if="submitMessage" class="success">{{ submitMessage }}</p>
      <p v-if="submitError" class="error-msg">{{ submitError }}</p>
    </section>
  </div>
</template>

<style scoped>
.page h1 {
  font-family: var(--font-display);
  font-size: 2rem;
  margin: 0 0 0.35rem;
}
.intro {
  margin: 0 0 1.5rem;
}
.intro code {
  font-size: 0.85em;
  padding: 0.15em 0.4em;
  border-radius: 6px;
  background: var(--surface2);
  border: 1px solid var(--border);
}
.intro strong {
  color: var(--accent);
}
.section {
  margin-bottom: 1.5rem;
}
.section h2 {
  margin: 0 0 0.5rem;
  font-size: 1.15rem;
}
.hint {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
}
.tiny {
  font-size: 0.85rem;
  margin: 0.5rem 0 0;
}
.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.search-wrap input {
  flex: 1;
  min-width: 200px;
}
.search-status {
  font-size: 0.85rem;
  color: var(--muted);
  white-space: nowrap;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.results {
  list-style: none;
  margin: 1rem 0 0;
  padding: 0;
  max-height: 320px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg);
}
.movie-row {
  width: 100%;
  text-align: left;
  padding: 0.75rem 1rem;
  border: none;
  border-bottom: 1px solid var(--border);
  background: transparent;
  color: inherit;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  font-family: inherit;
}
.movie-row:last-child {
  border-bottom: none;
}
.movie-row:hover {
  background: var(--surface2);
}
.movie-row.active {
  background: rgba(52, 211, 153, 0.12);
  border-left: 3px solid var(--accent-dim);
}
.title {
  font-weight: 600;
}
.small {
  font-size: 0.8rem;
}
textarea {
  margin-bottom: 0.75rem;
  resize: vertical;
}
.success {
  margin-top: 0.75rem;
  color: var(--accent-dim);
  font-size: 0.9rem;
}
</style>
