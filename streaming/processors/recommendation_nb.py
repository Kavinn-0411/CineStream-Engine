"""Multinomial Naive Bayes recommendations (content + user token features).

Trained offline by ``scripts/train_recommendation_nb.py``; scored in the Spark
driver each micro-batch (demo scale). Falls back to heuristic when model path
unset or missing (handled in ``streaming.main``).
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, StructField, StructType

from streaming.config import StreamingConfig
from streaming.recommendation_text import training_example_text


def _empty_recommendations_df(spark) -> DataFrame:
    schema = StructType(
        [
            StructField("user_id", IntegerType(), False),
            StructField("movie_id", IntegerType(), False),
            StructField("score", DoubleType(), False),
        ]
    )
    return spark.createDataFrame([], schema)


def build_nb_recommendations(
    scored_reviews_df: DataFrame, cfg: StreamingConfig, top_n: int = 10
) -> DataFrame:
    """
    Cross-join impacted users with all movies (excluding already reviewed),
    score each row with sklearn MultinomialNB ``predict_proba`` for the
    positive class (liked), take top-N per user.
    """
    spark = scored_reviews_df.sparkSession
    model_path = Path(cfg.recommendation_nb_model_path)
    if not model_path.is_file():
        raise FileNotFoundError(f"NB model not found: {model_path}")

    pipeline = joblib.load(model_path)
    jdbc = {
        "url": cfg.mysql_jdbc_url,
        "user": cfg.mysql_user,
        "password": cfg.mysql_password,
        "driver": "com.mysql.cj.jdbc.Driver",
    }

    movies_df = spark.read.format("jdbc").options(**jdbc, dbtable="movies").load()
    user_pref_df = spark.read.format("jdbc").options(**jdbc, dbtable="user_preferences").load()

    impacted_users = scored_reviews_df.select("user_id").distinct()
    if impacted_users.limit(1).count() == 0:
        return _empty_recommendations_df(spark)

    reviewed = user_pref_df.select("user_id", "movie_id").distinct()
    candidates = impacted_users.crossJoin(
        movies_df.select("movie_id", "title", "imdb_rating", "genres")
    )
    filtered = candidates.join(reviewed, on=["user_id", "movie_id"], how="left_anti")

    pdf = filtered.select(
        F.col("user_id").cast("int"),
        F.col("movie_id").cast("int"),
        F.col("genres").cast("string"),
        F.col("title").cast("string"),
    ).toPandas()

    if pdf.empty:
        return _empty_recommendations_df(spark)

    texts = [
        training_example_text(int(r.user_id), r.genres, r.title) for r in pdf.itertuples(index=False)
    ]
    proba = pipeline.predict_proba(texts)
    classes = list(getattr(pipeline, "classes_", [0, 1]))
    if proba.shape[1] < 2:
        pdf["score"] = 0.5
    elif 1 in classes:
        pos_idx = classes.index(1)
        pdf["score"] = proba[:, pos_idx].astype(float)
    else:
        pdf["score"] = proba[:, -1].astype(float)

    pdf = pdf.sort_values(["user_id", "score"], ascending=[True, False])
    pdf = pdf.groupby("user_id", as_index=False).head(top_n)
    pdf["score"] = pdf["score"].round(4)

    schema = StructType(
        [
            StructField("user_id", IntegerType(), False),
            StructField("movie_id", IntegerType(), False),
            StructField("score", DoubleType(), False),
        ]
    )
    return spark.createDataFrame(pdf[["user_id", "movie_id", "score"]], schema=schema)
