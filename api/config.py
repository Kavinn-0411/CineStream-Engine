"""
CineStream API Configuration
Loads settings from environment variables
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_TITLE: str = "CineStream API"
    API_DESCRIPTION: str = "Real-time movie recommendation engine"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # MySQL Configuration
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3307
    MYSQL_DB: str = "cinestream"
    MYSQL_USER: str = "cinestream_user"
    MYSQL_PASSWORD: str = "cinestream_password"
    MYSQL_POOL_SIZE: int = 5
    
    # MongoDB Configuration
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DB: str = "cinestream_logs"
    MONGODB_USER: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_REVIEWS: str = "reviews"
    KAFKA_TOPIC_MOVIE_LOGS: str = "movie-logs"
    
    # Recommendation Configuration
    RECOMMENDATION_TOP_N: int = 10
    RECOMMENDATION_MIN_SCORE: float = 0.1
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields from .env that aren't defined here
    )


# Global settings instance
settings = Settings()
