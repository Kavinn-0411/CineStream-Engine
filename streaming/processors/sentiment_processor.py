"""Model-based sentiment processing for review text.

Uses mapInPandas so the Hugging Face pipeline (weights) is loaded ONCE per Spark
partition, not once per row. Plain Python UDFs often re-initialize or run in
contexts where a module-level cache does not survive — that looks like
"loading weights every inference" and is unnecessarily slow.
"""

from __future__ import annotations

import pandas as pd
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"


def _sentiment_map_partitions(iterator):
    """
    One iterator = one Spark partition. Load the model once at partition start,
    then score every row in all pandas chunks for this partition.

    WEIGHT LOAD TRIGGER: the line below runs once *per partition*. If you see
    3–4 loads for one batch, Spark used 3–4 partitions (e.g. local[*] defaults).
    Use coalesce(1) or SENTIMENT_INFERENCE_PARTITIONS=1 to force a single load.
    """
    from transformers import pipeline

    clf = pipeline("sentiment-analysis", model=MODEL_NAME)  # <-- loads HF weights (once per partition)

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

        texts = pdf["review_text"].fillna("").astype(str).str.slice(0, 512)
        labels: list[str] = []
        scores: list[float] = []

        for t in texts:
            if not t or not str(t).strip():
                labels.append("neutral")
                scores.append(0.0)
                continue
            pred = clf(str(t))[0]
            label = str(pred["label"]).lower()
            sc = float(pred["score"])
            if label == "positive":
                labels.append("positive")
                scores.append(max(min(sc, 1.0), -1.0))
            else:
                labels.append("negative")
                scores.append(max(min(-sc, 1.0), -1.0))

        out = pdf.copy()
        out["sentiment_label"] = labels
        out["sentiment_score"] = scores
        out["derived_rating"] = (
            ((out["sentiment_score"].astype(float) + 1.0) / 2.0) * 5.0
        ).round(2)
        yield out


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


def add_sentiment_columns(df: DataFrame, sentiment_partitions: int = 1) -> DataFrame:
    """
    Attach sentiment_label, sentiment_score, derived_rating.
    Model loads once per Spark partition (see pipeline() inside _sentiment_map_partitions).
    """
    # Ensure column order matches schema for mapInPandas (stable layout)
    ordered = df.select(
        "event_id",
        "user_id",
        "movie_id",
        "review_text",
        "event_time",
        "source",
    )
    if sentiment_partitions and sentiment_partitions > 0:
        ordered = ordered.coalesce(sentiment_partitions)
    return ordered.mapInPandas(_sentiment_map_partitions, schema=_output_schema())
