"""Model-based sentiment processing for review text."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

from transformers import pipeline


MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
_sentiment_pipeline = None


def _get_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        _sentiment_pipeline = pipeline("sentiment-analysis", model=MODEL_NAME)
    return _sentiment_pipeline


def _infer_sentiment(text: str):
    if not text or not text.strip():
        return ("neutral", 0.0)

    clf = _get_pipeline()
    pred = clf(text[:512])[0]
    label = str(pred["label"]).lower()
    score = float(pred["score"])

    # Convert to symmetric score in range [-1, 1]
    if label == "positive":
        sentiment_score = score
        sentiment_label = "positive"
    else:
        sentiment_score = -score
        sentiment_label = "negative"

    return (sentiment_label, max(min(sentiment_score, 1.0), -1.0))


def add_sentiment_columns(df: DataFrame) -> DataFrame:
    sentiment_schema = StructType(
        [
            StructField("sentiment_label", StringType(), True),
            StructField("sentiment_score", DoubleType(), True),
        ]
    )

    sentiment_udf = F.udf(_infer_sentiment, sentiment_schema)

    enriched = df.withColumn("sentiment_struct", sentiment_udf(F.col("review_text")))
    with_scores = (
        enriched.withColumn("sentiment_label", F.col("sentiment_struct.sentiment_label"))
        .withColumn("sentiment_score", F.col("sentiment_struct.sentiment_score"))
        .drop("sentiment_struct")
    )

    return with_scores.withColumn(
        "derived_rating",
        F.round(((F.col("sentiment_score") + F.lit(1.0)) / F.lit(2.0)) * F.lit(5.0), 2),
    )
