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
2. **Home** — `GET /api/v1/me/recommendations` (Bearer) when Spark has written rows; otherwise the welcome message.
3. **Search & review** (`/dashboard`) — live-search movies, then `POST /api/v1/reviews` with JWT only (`movie_id` + `review_text`).

Auth: **JWT** from `POST /api/v1/auth/login` or `/auth/register`, stored in `localStorage` under `cinestream_auth` with the `Authorization: Bearer` header on API calls. Reviews use `POST /api/v1/reviews` with **no** `user_id` in the body (it comes from the token). Home loads `GET /api/v1/me/recommendations`.
