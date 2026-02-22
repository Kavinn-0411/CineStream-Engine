-- CineStream MySQL Database Schema

-- Create database if not exists (already created by MYSQL_DATABASE env var, but included for safety)
CREATE DATABASE IF NOT EXISTS cinestream CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cinestream;

-- Movies table
-- Note: movie_id should match the ID from the CSV dataset
-- This table will be populated from CSV file
CREATE TABLE IF NOT EXISTS movies (
    movie_id INT PRIMARY KEY,  -- ID from CSV, not auto-increment
    title VARCHAR(500) NOT NULL,
    imdb_rating DECIMAL(3, 1),
    genres VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users table (password_hash = bcrypt)
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Raw reviews table (ingestion source-of-truth for streaming)
CREATE TABLE IF NOT EXISTS reviews_raw (
    review_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_id CHAR(36) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    review_text TEXT NOT NULL,
    event_time DATETIME(6) NOT NULL,
    kafka_topic VARCHAR(100) DEFAULT NULL,
    kafka_published TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User preferences table (ratings derived from sentiment analysis)
CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    rating DECIMAL(3, 2) NOT NULL,
    sentiment_score DECIMAL(3, 2),
    last_review_text TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_movie (user_id, movie_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    CONSTRAINT chk_rating CHECK (rating >= 0.0 AND rating <= 5.0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    score DECIMAL(5, 4) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_movie_recommendation (user_id, movie_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Indexes for performance
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_movie_id ON user_preferences(movie_id);
CREATE INDEX idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX idx_recommendations_score ON recommendations(user_id, score DESC);
CREATE INDEX idx_movies_genres ON movies(genres(255));
CREATE INDEX idx_movies_title ON movies(title(255));
CREATE INDEX idx_reviews_raw_user_id ON reviews_raw(user_id);
CREATE INDEX idx_reviews_raw_movie_id ON reviews_raw(movie_id);
CREATE INDEX idx_reviews_raw_event_time ON reviews_raw(event_time DESC);
CREATE INDEX idx_reviews_raw_kafka_published ON reviews_raw(kafka_published);

-- Seed one test user for early local development (password: testpass123).
INSERT INTO users (user_id, username, email, password_hash)
VALUES (
    1,
    'test_user_1',
    'test_user_1@cinestream.local',
    '$2b$12$tqQqKmF/0jYb4UpFziOiguwtsegOIuPtVEWBctiR8BbdHVNIfLrI2'
)
ON DUPLICATE KEY UPDATE
    username = VALUES(username),
    email = VALUES(email),
    password_hash = VALUES(password_hash);

