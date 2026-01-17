"""
Database Connection Management
Provides connection pools for MySQL and MongoDB
"""

import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import Optional
import logging

from api.config import settings

logger = logging.getLogger(__name__)

# MySQL Connection Pool
_mysql_pool: Optional[pooling.MySQLConnectionPool] = None

# MongoDB Client
_mongo_client: Optional[MongoClient] = None
_mongo_db = None


def initialize_mysql_pool():
    """Initialize MySQL connection pool"""
    global _mysql_pool
    
    try:
        _mysql_pool = pooling.MySQLConnectionPool(
            pool_name="cinestream_pool",
            pool_size=settings.MYSQL_POOL_SIZE,
            pool_reset_session=True,
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            database=settings.MYSQL_DB,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            autocommit=False
        )
        logger.info(f"MySQL connection pool initialized: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}")
        return True
    except MySQLError as e:
        logger.error(f"Failed to initialize MySQL connection pool: {e}")
        return False


def get_mysql_connection():
    """
    Get a connection from MySQL pool
    Returns: mysql.connector.connection.MySQLConnection
    """
    global _mysql_pool
    
    if _mysql_pool is None:
        initialize_mysql_pool()
    
    try:
        connection = _mysql_pool.get_connection()
        return connection
    except MySQLError as e:
        logger.error(f"Failed to get MySQL connection from pool: {e}")
        raise


def test_mysql_connection() -> bool:
    """Test MySQL connectivity"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] == 1
    except Exception as e:
        logger.error(f"MySQL connection test failed: {e}")
        return False


def initialize_mongodb():
    """Initialize MongoDB connection"""
    global _mongo_client, _mongo_db
    
    try:
        # Build connection string
        if settings.MONGODB_USER and settings.MONGODB_PASSWORD:
            # Connect with authentication
            connection_string = (
                f"mongodb://{settings.MONGODB_USER}:{settings.MONGODB_PASSWORD}@"
                f"{settings.MONGODB_HOST}:{settings.MONGODB_PORT}/"
                f"{settings.MONGODB_DB}?authSource={settings.MONGODB_DB}"
            )
        else:
            # Connect without authentication (for development)
            connection_string = f"mongodb://{settings.MONGODB_HOST}:{settings.MONGODB_PORT}/"
        
        _mongo_client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        _mongo_client.admin.command('ping')
        
        _mongo_db = _mongo_client[settings.MONGODB_DB]
        logger.info(f"MongoDB connection initialized: {settings.MONGODB_HOST}:{settings.MONGODB_PORT}/{settings.MONGODB_DB}")
        return True
    except ConnectionFailure as e:
        logger.error(f"Failed to initialize MongoDB connection: {e}")
        return False
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        return False


def get_mongo_db():
    """
    Get MongoDB database instance
    Returns: pymongo.database.Database
    """
    global _mongo_db
    
    if _mongo_db is None:
        initialize_mongodb()
    
    return _mongo_db


def test_mongodb_connection() -> bool:
    """Test MongoDB connectivity"""
    try:
        db = get_mongo_db()
        db.command('ping')
        return True
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {e}")
        return False


def close_connections():
    """Close all database connections"""
    global _mongo_client
    
    if _mongo_client:
        _mongo_client.close()
        logger.info("MongoDB connection closed")
    
    # MySQL connection pool doesn't need explicit closing
    logger.info("Database connections closed")
