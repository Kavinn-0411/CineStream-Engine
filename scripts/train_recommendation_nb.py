"""
Train Multinomial Naive Bayes recommender (TfidfVectorizer + MultinomialNB).

Labels: liked (1) if user_preferences.rating >= 3 else 0.
Features: same string as streaming.recommendation_text.training_example_text.

Usage (from repo root, with MySQL up and .env loaded):
    python scripts/train_recommendation_nb.py
    python scripts/train_recommendation_nb.py --output models/artifacts/recommendation_mnb.joblib
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Repo root on path for `streaming` package
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import mysql.connector
from dotenv import load_dotenv
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from streaming.recommendation_text import training_example_text


def _connect():
    load_dotenv(ROOT / ".env")
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3307")),
        database=os.getenv("MYSQL_DB", "cinestream"),
        user=os.getenv("MYSQL_USER", "cinestream_user"),
        password=os.getenv("MYSQL_PASSWORD", "cinestream_password"),
    )


def load_training_frame(conn) -> pd.DataFrame:
    q = """
        SELECT up.user_id, up.movie_id, up.rating, m.genres, m.title
        FROM user_preferences up
        INNER JOIN movies m ON up.movie_id = m.movie_id
    """
    return pd.read_sql(q, conn)


def augment_if_needed(df: pd.DataFrame, conn) -> pd.DataFrame:
    """Ensure at least two classes and a few rows so NB + TF-IDF can fit."""
    if df.empty:
        # Pull random movies and synthetic users for a cold-start artifact
        movies = pd.read_sql(
            "SELECT movie_id, genres, title FROM movies LIMIT 200", conn
        )
        if movies.empty:
            raise RuntimeError("No movies in database — load movies CSV first.")
        rows = []
        for i, r in movies.head(50).iterrows():
            rows.append(
                {
                    "user_id": 1,
                    "movie_id": int(r["movie_id"]),
                    "rating": 4.0 if i % 2 == 0 else 2.0,
                    "genres": r["genres"],
                    "title": r["title"],
                }
            )
        return pd.DataFrame(rows)

    df = df.copy()
    df["y"] = (df["rating"] >= 3.0).astype(int)
    if df["y"].nunique() < 2 or len(df) < 8:
        # Add cheap negatives: same user, random movies they did not rate highly
        extra = pd.read_sql(
            "SELECT movie_id, genres, title FROM movies ORDER BY RAND() LIMIT 80",
            conn,
        )
        uid = int(df["user_id"].mode().iloc[0]) if len(df) else 1
        seen = set(zip(df["user_id"], df["movie_id"]))
        for _, r in extra.iterrows():
            mid = int(r["movie_id"])
            if (uid, mid) in seen:
                continue
            seen.add((uid, mid))
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [
                            {
                                "user_id": uid,
                                "movie_id": mid,
                                "rating": 2.0,
                                "genres": r["genres"],
                                "title": r["title"],
                                "y": 0,
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )
            if len(df) >= 12 and df["y"].nunique() >= 2:
                break
        if df["y"].nunique() < 2:
            df["y"] = (df["rating"] >= df["rating"].median()).astype(int)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Train NB recommender pipeline")
    parser.add_argument(
        "--output",
        default=str(ROOT / "models" / "artifacts" / "recommendation_mnb.joblib"),
        help="Where to write the joblib pipeline",
    )
    args = parser.parse_args()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = _connect()
    try:
        raw = load_training_frame(conn)
        df = augment_if_needed(raw, conn)
        if "y" not in df.columns:
            df["y"] = (df["rating"] >= 3.0).astype(int)

        texts = [
            training_example_text(int(row["user_id"]), row.get("genres"), row.get("title"))
            for _, row in df.iterrows()
        ]
        y = df["y"].astype(int).values

        pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        max_features=8000,
                        ngram_range=(1, 2),
                        min_df=1,
                        strip_accents="unicode",
                    ),
                ),
                ("clf", MultinomialNB(alpha=0.1)),
            ]
        )
        pipeline.fit(texts, y)
        joblib.dump(pipeline, out_path)
        print(f"Wrote {out_path} (n_samples={len(texts)}, classes={list(pipeline.classes_)})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
