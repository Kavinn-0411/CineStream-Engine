# CineStream Vue frontend

Vue 3 + Vite UI for multi-user demos: **Home** (recommendations or welcome copy) and **Dashboard** (movie search + reviews).

## Run

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — API requests use the Vite proxy to `http://127.0.0.1:8000` by default.

If the API runs elsewhere, copy `.env.example` to `.env` and set `VITE_API_BASE_URL` to that origin (and add it to FastAPI `CORSMiddleware` in `api/main.py`).

## Flow

1. **Register** or **Sign in** (username lookup).
2. **Home** — shows recommendations from `GET /api/v1/recommendations/{user_id}` when Spark has written rows; otherwise the “Movie Buff community” message.
3. **Search & review** (`/dashboard`) — type a title to live-search movies (`GET /api/v1/movies?search=...`), pick one, then `POST /api/v1/reviews` with your `user_id`.

Auth is **sessionless**: user id/username are stored in `localStorage` (demo only).
