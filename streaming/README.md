# Streaming Job (Kafka → PySpark → MySQL)

Consumes review events from Kafka, scores **sentiment** with a **trained Multinomial Naive Bayes** pipeline (TF‑IDF features), upserts **`user_preferences`**, then builds **heuristic** top‑N **recommendations** (genre affinity + IMDb) and upserts **`recommendations`**.

## Current behavior

1. Reads from Kafka topic: `KAFKA_TOPIC_REVIEWS` (default `reviews`)
2. Parses JSON review events
3. **Sentiment:** `TfidfVectorizer` + `MultinomialNB` loaded from `SENTIMENT_MNB_MODEL_PATH` (default `models/artifacts/sentiment_mnb.joblib`).  
   - `predict_proba` → positive class probability `p` → `derived_rating = round(p * 5, 2)`, `sentiment_score = 2p - 1`, label positive/negative/neutral for empty text.
4. Upserts `(user_id, movie_id)` into MySQL `user_preferences`
5. **Recommendations:** genre + IMDb heuristic only (`recommendation_processor.py`)

## Train sentiment NB (your data)

CSV (or TSV) must have a **text** column and a **label** column. Defaults: `review_text`, `sentiment`. Labels: `positive` / `negative` (or `1` / `0`).

```bash
python scripts/train_sentiment_nb.py --data path/to/your_download.csv
python scripts/train_sentiment_nb.py --data ./reviews.csv --text-col text --label-col polarity
```

Requires at least **4** cleaned rows and **both** classes after normalization.

## Run

```bash
pip install pyarrow
python -m streaming.main
```

The job **exits immediately** if the sentiment joblib file is missing (train first).

## Required services

- Kafka at `KAFKA_BOOTSTRAP_SERVERS`
- MySQL at `MYSQL_HOST:MYSQL_PORT`
- Topic receives events from `POST /api/v1/reviews`

## Verify end-to-end

```sql
SELECT user_id, movie_id, rating, sentiment_score, updated_at
FROM user_preferences
ORDER BY updated_at DESC
LIMIT 20;
```

## Next upgrade

- Collaborative filtering or learned rankers for recommendations
- MongoDB processing logs
