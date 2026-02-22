"""Sentiment scoring for review text using a trained Multinomial Naive Bayes pipeline.

Train offline with your labeled CSV:
    python scripts/train_sentiment_nb.py --data path/to/your_download.csv

Uses mapInPandas so the sklearn ``joblib`` artifact loads ONCE per Spark partition.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pyspark.sql import DataFrame
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from streaming.config import StreamingConfig


def _positive_proba_column(pipeline) -> int:
    """Index into predict_proba[:, i] for the positive class (handles np.int64 labels)."""
    clf = pipeline.named_steps.get("clf") if hasattr(pipeline, "named_steps") else pipeline
    classes = list(getattr(clf, "classes_", getattr(pipeline, "classes_", [0, 1])))
    for i, c in enumerate(classes):
        try:
            if int(c) == 1:
                return i
        except (TypeError, ValueError):
            continue
    for i, c in enumerate(classes):
        if str(c).lower() in ("positive", "pos", "true"):
            return i
    return len(classes) - 1


def _nb_sentiment_map_fn(model_path: str):
    """Build picklable mapInPandas closure (path captured for workers)."""

    def _iterator(iterator):
        import joblib

        path = Path(model_path)
        clf = joblib.load(path) if path.is_file() else None

        for pdf in iterator:
            if pdf is None:
                continue
            if pdf.empty:
                yield pdf.assign(
                    sentiment_label=pd.Series(dtype=str),
                    sentiment_score=pd.Series(dtype=float),
                    derived_rating=pd.Series(dtype=float),
                )
                continue

            texts = pdf["review_text"].fillna("").astype(str).str.slice(0, 8192).reset_index(drop=True)
            n = len(texts)
            labels: list[str] = []
            scores: list[float] = []
            ratings: list[float] = []

            if clf is None:
                for _ in range(n):
                    labels.append("neutral")
                    scores.append(0.0)
                    ratings.append(2.5)
            else:
                pos_idx = _positive_proba_column(clf)
                empty_mask = texts.str.strip() == ""
                nonempty = ~empty_mask
                proba_pos = pd.Series(0.5, index=texts.index)
                if nonempty.any():
                    proba = clf.predict_proba(texts.loc[nonempty].tolist())
                    proba_pos.loc[nonempty] = proba[:, pos_idx]
                # sentiment_score in [-1, 1]: 2p - 1
                sscore = (proba_pos * 2.0 - 1.0).clip(-1.0, 1.0)
                for i, t in enumerate(texts):
                    if str(t).strip() == "":
                        labels.append("neutral")
                        scores.append(0.0)
                        ratings.append(2.5)
                    else:
                        p = float(proba_pos.iloc[i])
                        labels.append("positive" if p >= 0.5 else "negative")
                        scores.append(float(sscore.iloc[i]))
                        ratings.append(round(p * 5.0, 2))

            out = pdf.copy()
            out["sentiment_label"] = labels
            out["sentiment_score"] = scores
            out["derived_rating"] = ratings
            yield out

    return _iterator


def _output_schema() -> StructType:
    return StructType(
        [
            StructField("event_id", StringType(), True),
            StructField("user_id", IntegerType(), True),
            StructField("movie_id", IntegerType(), True),
            StructField("review_text", StringType(), True),
            StructField("event_time", TimestampType(), True),
            StructField("source", StringType(), True),
            StructField("sentiment_label", StringType(), True),
            StructField("sentiment_score", DoubleType(), True),
            StructField("derived_rating", DoubleType(), True),
        ]
    )


def add_sentiment_columns(
    df: DataFrame,
    cfg: StreamingConfig,
    sentiment_partitions: int = 1,
) -> DataFrame:
    """
    Attach sentiment_label, sentiment_score, derived_rating using
    ``cfg.sentiment_nb_model_path`` (TfidfVectorizer + MultinomialNB joblib).
    """
    ordered = df.select(
        "event_id",
        "user_id",
        "movie_id",
        "review_text",
        "event_time",
        "source",
    )
    fn = _nb_sentiment_map_fn(cfg.sentiment_nb_model_path)
    if sentiment_partitions and sentiment_partitions > 0:
        ordered = ordered.coalesce(sentiment_partitions)
    return ordered.mapInPandas(fn, schema=_output_schema())
