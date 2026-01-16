"""
CineStream API - Main Application
Real-time movie recommendation engine backend
"""

from fastapi import FastAPI, status
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
    close_connections
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
    close_connections()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
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
        "health": "/health"
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
                "database": settings.MYSQL_DB
            },
            "mongodb": {
                "status": "connected" if mongodb_status else "disconnected",
                "host": settings.MONGODB_HOST,
                "port": settings.MONGODB_PORT,
                "database": settings.MONGODB_DB
            },
            "kafka": {
                "status": "not_tested",
                "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "note": "Kafka connectivity will be tested when producer is initialized"
            }
        }
    }
    
    if not is_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response
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
            "mongodb": mongodb_info
        }
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
