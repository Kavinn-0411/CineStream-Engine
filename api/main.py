"""
CineStream API - Main Application
Real-time movie recommendation engine backend
"""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from api.config import settings
from api.database.connection import (
    initialize_mysql_pool,
    initialize_mongodb,
    test_mysql_connection,
    test_mongodb_connection,
    close_connections,
)
from api.deps import get_current_user_id, get_current_user_row
from api.kafka.producer import close_kafka_producer
from api.processor import (
    create_movie_processor,
    create_review_processor,
    delete_movie_processor,
    get_movie_processor,
    get_recommendations_processor,
    get_user_by_id_processor,
    list_movies_processor,
    list_users_processor,
    login_user_processor,
    register_and_token_processor,
    update_movie_processor,
)
from api.schemas.movie import MovieCreate, MovieListResponse, MovieResponse, MovieUpdate
from api.schemas.recommendation import RecommendationListResponse
from api.schemas.review import ReviewCreate, ReviewCreateResponse
from api.schemas.user import (
    TokenResponse,
    UserCreate,
    UserListResponse,
    UserLogin,
    UserResponse,
)
from api.utils.logger import setup_logging


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    Handles startup and shutdown
    """
    # Startup
    logger.info("Starting CineStream API...")

    # Initialize database connections
    mysql_ok = initialize_mysql_pool()
    mongodb_ok = initialize_mongodb()

    if mysql_ok:
        logger.info("✓ MySQL connection pool ready")
    else:
        logger.error("✗ MySQL connection failed")

    if mongodb_ok:
        logger.info("✓ MongoDB connection ready")
    else:
        logger.error("✗ MongoDB connection failed")

    logger.info(f"API running at http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"Swagger docs at http://{settings.API_HOST}:{settings.API_PORT}/docs")

    yield

    # Shutdown
    logger.info("Shutting down CineStream API...")
    close_kafka_producer()
    close_connections()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint - API information"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


# Health check endpoint
@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
def health_check():
    """
    Health check endpoint
    Verifies database connectivity and system status
    """
    # Test database connections
    mysql_status = test_mysql_connection()
    mongodb_status = test_mongodb_connection()

    # Overall health
    is_healthy = mysql_status and mongodb_status

    response = {
        "status": "healthy" if is_healthy else "unhealthy",
        "services": {
            "mysql": {
                "status": "connected" if mysql_status else "disconnected",
                "host": settings.MYSQL_HOST,
                "port": settings.MYSQL_PORT,
                "database": settings.MYSQL_DB,
            },
            "mongodb": {
                "status": "connected" if mongodb_status else "disconnected",
                "host": settings.MONGODB_HOST,
                "port": settings.MONGODB_PORT,
                "database": settings.MONGODB_DB,
            },
            "kafka": {
                "status": "not_tested",
                "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "note": "Kafka connectivity will be tested when producer is initialized",
            },
        },
    }

    if not is_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response,
        )

    return response


# Database status endpoint
@app.get("/status/database", tags=["Status"])
def database_status():
    """Check detailed database status"""
    try:
        from api.database.connection import get_mysql_connection, get_mongo_db

        # MySQL info
        mysql_info = {}
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            # Get table counts
            cursor.execute("SELECT COUNT(*) FROM movies")
            mysql_info["movies_count"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users")
            mysql_info["users_count"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM user_preferences")
            mysql_info["preferences_count"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM recommendations")
            mysql_info["recommendations_count"] = cursor.fetchone()[0]

            cursor.close()
            conn.close()
            mysql_info["status"] = "connected"
        except Exception as e:
            mysql_info["status"] = "error"
            mysql_info["error"] = str(e)

        # MongoDB info
        mongodb_info = {}
        try:
            db = get_mongo_db()
            mongodb_info["collections"] = db.list_collection_names()
            mongodb_info["review_logs_count"] = db.review_logs.count_documents({})
            mongodb_info["streaming_logs_count"] = db.streaming_logs.count_documents({})
            mongodb_info["status"] = "connected"
        except Exception as e:
            mongodb_info["status"] = "error"
            mongodb_info["error"] = str(e)

        return {
            "mysql": mysql_info,
            "mongodb": mongodb_info,
        }
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)},
        )


# Auth (JWT + password)
@app.post(
    "/api/v1/auth/register",
    tags=["Auth"],
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def auth_register(payload: UserCreate):
    """Create account and return JWT."""
    return register_and_token_processor(payload)


@app.post(
    "/api/v1/auth/login",
    tags=["Auth"],
    response_model=TokenResponse,
)
def auth_login(payload: UserLogin):
    """Sign in with username + password; returns JWT."""
    return login_user_processor(payload)


@app.get(
    "/api/v1/users/me",
    tags=["Users"],
    response_model=UserResponse,
)
def users_me(user_row: Annotated[dict, Depends(get_current_user_row)]):
    """Current user from Bearer token."""
    return UserResponse(**user_row)


@app.get(
    "/api/v1/me/recommendations",
    tags=["Recommendations"],
    response_model=RecommendationListResponse,
)
def my_recommendations_endpoint(
    user_id: Annotated[int, Depends(get_current_user_id)],
    limit: int = Query(
        default=settings.RECOMMENDATION_TOP_N,
        ge=1,
        le=50,
        description="Max items to return",
    ),
):
    """Recommendations for the authenticated user only."""
    return get_recommendations_processor(user_id, limit=limit)


# Users (public list / profile by id — no passwords exposed)
@app.get(
    "/api/v1/users",
    tags=["Users"],
    response_model=UserListResponse,
)
def list_users_endpoint(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * size
    return list_users_processor(limit=size, offset=offset)


@app.get(
    "/api/v1/users/{user_id}",
    tags=["Users"],
    response_model=UserResponse,
)
def get_user_by_id_endpoint(user_id: int):
    return get_user_by_id_processor(user_id)


# Movie CRUD endpoints (Phase 2)
@app.post(
    "/api/v1/movies",
    tags=["Movies"],
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_movie_endpoint(payload: MovieCreate):
    return create_movie_processor(payload)


@app.get(
    "/api/v1/movies/{movie_id}",
    tags=["Movies"],
    response_model=MovieResponse,
)
def get_movie_endpoint(movie_id: int):
    return get_movie_processor(movie_id)


@app.get(
    "/api/v1/movies",
    tags=["Movies"],
    response_model=MovieListResponse,
)
def list_movies_endpoint(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    genre: str | None = None,
):
    return list_movies_processor(page=page, size=size, search=search, genre=genre)


@app.put(
    "/api/v1/movies/{movie_id}",
    tags=["Movies"],
    response_model=MovieResponse,
)
def update_movie_endpoint(movie_id: int, payload: MovieUpdate):
    return update_movie_processor(movie_id, payload)


@app.delete(
    "/api/v1/movies/{movie_id}",
    tags=["Movies"],
)
def delete_movie_endpoint(movie_id: int):
    return delete_movie_processor(movie_id)


@app.post(
    "/api/v1/reviews",
    tags=["Reviews"],
    response_model=ReviewCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review_endpoint(
    payload: ReviewCreate,
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Submit a review (user id is taken from JWT, not the request body)."""
    return create_review_processor(payload, user_id)


@app.get(
    "/api/v1/recommendations/{user_id}",
    tags=["Recommendations"],
    response_model=RecommendationListResponse,
)
def get_recommendations_endpoint(
    user_id: int,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    limit: int = Query(
        default=settings.RECOMMENDATION_TOP_N,
        ge=1,
        le=50,
        description="Max items to return",
    ),
):
    """
    Return stored recommendations for a user (must match the JWT subject).
    Prefer GET /api/v1/me/recommendations from clients.
    """
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's recommendations.",
        )
    return get_recommendations_processor(user_id, limit=limit)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
