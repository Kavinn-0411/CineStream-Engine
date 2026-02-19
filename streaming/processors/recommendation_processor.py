"""Recommendation generation helpers for streaming pipeline."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from streaming.config import StreamingConfig


def build_candidate_recommendations(
    scored_reviews_df: DataFrame, cfg: StreamingConfig, top_n: int = 10
) -> DataFrame:
    """
    Build lightweight recommendation candidates from movies table + genre affinity.
    Strategy:
    - infer user preferred genres from positively scored reviews
    - exclude already reviewed movies
    - rank by genre match + imdb rating
    """
    spark = scored_reviews_df.sparkSession
    movies_df = spark.read.format("jdbc").options(
        url=cfg.mysql_jdbc_url,
        dbtable="movies",
        user=cfg.mysql_user,
        password=cfg.mysql_password,
        driver="com.mysql.cj.jdbc.Driver",
    ).load()

    # Users impacted in this micro-batch
    impacted_users = scored_reviews_df.select("user_id").distinct()

    # All user reviewed movies (from preferences table)
    user_pref_df = spark.read.format("jdbc").options(
        url=cfg.mysql_jdbc_url,
        dbtable="user_preferences",
        user=cfg.mysql_user,
        password=cfg.mysql_password,
        driver="com.mysql.cj.jdbc.Driver",
    ).load()

    # Preferred genres from positive ratings only, based on reviewed movies' genres.
    user_pref_with_genres = user_pref_df.join(
        movies_df.select("movie_id", "genres"), on="movie_id", how="left"
    )
    preferred = (
        user_pref_with_genres.filter(F.col("rating") >= 3.0)
        .withColumn("genre", F.explode(F.split(F.coalesce(F.col("genres"), F.lit("")), ",")))
        .withColumn("genre", F.lower(F.trim(F.col("genre"))))
        .filter(F.col("genre") != "")
        .groupBy("user_id", "genre")
        .agg(F.count("*").alias("genre_weight"))
    )

    # Fallback if no inferred genre: still rank by imdb_rating globally
    candidates = impacted_users.crossJoin(
        movies_df.select("movie_id", "title", "imdb_rating", "genres")
    ).withColumn("movie_genre", F.explode(F.split(F.coalesce(F.col("genres"), F.lit("")), ",")))
    candidates = candidates.withColumn("movie_genre", F.lower(F.trim(F.col("movie_genre"))))

    scored_candidates = (
        candidates.join(preferred, (candidates.user_id == preferred.user_id) & (candidates.movie_genre == preferred.genre), "left")
        .select(
            candidates.user_id,
            candidates.movie_id,
            candidates.imdb_rating,
            F.coalesce(F.col("genre_weight"), F.lit(0)).alias("genre_weight"),
        )
        .groupBy("user_id", "movie_id", "imdb_rating")
        .agg(F.max("genre_weight").alias("genre_weight"))
        .withColumn(
            "score",
            F.round(
                F.coalesce(F.col("imdb_rating"), F.lit(0.0)) * F.lit(0.6)
                + F.col("genre_weight") * F.lit(0.4),
                4,
            ),
        )
    )

    # Exclude already reviewed movies
    reviewed = user_pref_df.select("user_id", "movie_id").distinct()
    filtered = scored_candidates.join(reviewed, ["user_id", "movie_id"], "left_anti")

    # Top N per user
    window = Window.partitionBy("user_id").orderBy(F.desc("score"))
    ranked = filtered.withColumn("rank", F.row_number().over(window)).filter(F.col("rank") <= top_n)
    return ranked.select("user_id", "movie_id", "score")
