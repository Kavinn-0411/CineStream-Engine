# Streaming Job (Kafka -> PySpark -> MySQL)

This module consumes review events from Kafka, runs model-based sentiment scoring,
updates `user_preferences`, and writes candidate rows to `recommendations` in MySQL.

## Current behavior

1. Reads from Kafka topic: `KAFKA_TOPIC_REVIEWS` (default `reviews`)
2. Parses JSON review events
3. Computes sentiment with pre-trained Hugging Face model
4. Converts score to `derived_rating` on a 0..5 scale
5. Upserts `(user_id, movie_id)` into MySQL `user_preferences`
6. Builds top-N recommendations and upserts MySQL `recommendations`

### Recommendation scoring (Multinomial NB vs heuristic)

If `RECOMMENDATION_MNB_MODEL_PATH` (default: `models/artifacts/recommendation_mnb.joblib`) **exists**, each micro-batch scores candidates with a **sklearn** pipeline (`TfidfVectorizer` + `MultinomialNB`) trained on `user_preferences` joined to `movies` (liked = rating ≥ 3). If the file is missing, NB errors, or NB returns no rows, the job **falls back** to the genre + IMDb heuristic in `recommendation_processor.py`.

Train the model (MySQL must have `user_preferences` rows — submit a few reviews first, or the script augments from `movies`):

```bash
python scripts/train_recommendation_nb.py
```

## Run

Install **PyArrow** (required for `mapInPandas` sentiment scoring):

```bash
pip install pyarrow
```

Then:

```bash
python -m streaming.main
```

## Required services

- Kafka running at `KAFKA_BOOTSTRAP_SERVERS`
- MySQL running at `MYSQL_HOST:MYSQL_PORT`
- Topic exists and receives events from `POST /api/v1/reviews`

## Verify end-to-end

1. Start API and streaming job
2. Submit review via API
3. Check table:

```sql
SELECT user_id, movie_id, rating, sentiment_score, updated_at
FROM user_preferences
ORDER BY updated_at DESC
LIMIT 20;
```

## Next upgrade

- Per-user or matrix-factorization models; blend NB score with CF
- Add MongoDB processing logs
