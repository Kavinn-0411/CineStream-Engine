# CineStream Architecture & Data Flow

## Overview

CineStream is a real-time movie recommendation engine that personalizes suggestions based on user review history and sentiment analysis.

## Data Flow

```
CSV Movie Dataset → API (Movie Search/Lookup) → Frontend
                                                      ↓
User Reviews → API → Kafka → PySpark Streaming → Sentiment Analysis → User Preferences → Recommendations
                                                      ↓
                                              MySQL Database
```

## Components

### 1. Movie Dataset (CSV)
- **Location**: `data/movies.csv`
- **Purpose**: Source of truth for movie catalog
- **Usage**: 
  - Frontend reads CSV to display/search movies
  - API can load CSV into database for efficient querying
  - CSV structure: `movie_id, title, genre, release_year, imdb_id, ...`

### 2. API Service
- **Movie Endpoints**:
  - `GET /api/v1/movies/search?q={query}` - Search movies by title/genre
  - `GET /api/v1/movies/{movie_id}` - Get movie details
  - `GET /api/v1/movies` - List all movies (paginated)
  
- **Review Endpoints**:
  - `POST /api/v1/reviews` - Submit a text review for a movie
    - Body: `{user_id, movie_id, review_text}`
    - Publishes to Kafka `reviews` topic
  
- **Recommendation Endpoints**:
  - `GET /api/v1/recommendations/{user_id}` - Get personalized recommendations
    - Returns top-N movies based on user's review history

### 3. Kafka Topics
- **`reviews`**: User text reviews
  - Message format: `{user_id, movie_id, review_text, timestamp}`

### 4. PySpark Streaming Job
- **Input**: Consumes from Kafka `reviews` topic
- **Processing**:
  1. Extract reviews in micro-batches
  2. Perform sentiment analysis on `review_text`
  3. Convert sentiment to rating (0.0-5.0 scale)
  4. Update `user_preferences` table in MySQL
  5. Trigger recommendation generation for the user
  6. Store recommendations in `recommendations` table
  7. Log raw review to MongoDB

### 5. Database Schema (MySQL)

#### `movies` Table
- Populated from CSV dataset
- `movie_id` is the primary key (matches CSV ID)
- Used for movie lookups and recommendations

#### `users` Table
- Stores user information
- Created when first review is submitted

#### `user_preferences` Table
- Stores user-movie ratings derived from sentiment analysis
- Updated in real-time as reviews are processed
- Key for recommendation generation

#### `recommendations` Table
- Stores generated recommendations
- Updated when new reviews trigger recommendation recalculation

### 6. Recommendation Logic

1. **Input**: User's review history from `user_preferences` table
2. **Collaborative Filtering**: 
   - Find users with similar preferences
   - Identify movies liked by similar users
3. **Sentiment Weighting**: 
   - Prioritize movies similar to those with positive sentiment
4. **Filtering**:
   - Exclude movies user has already reviewed
   - Exclude movies with very low scores
5. **Output**: Top-N recommendations stored in database

## Workflow Example

1. **User searches for movie**: Frontend queries API → API searches movies table
2. **User submits review**: 
   - Frontend → API → Kafka `reviews` topic
   - PySpark consumes review → Sentiment analysis → Update `user_preferences`
   - Generate recommendations → Store in `recommendations` table
3. **User requests recommendations**: 
   - Frontend → API → Query `recommendations` table → Return top-N movies

## Movie Data Management

### Option 1: CSV → Database Sync (Recommended)
- Load CSV into `movies` table on startup or via script
- API queries database for fast search/lookup
- Periodic sync if CSV is updated

### Option 2: Direct CSV Access
- API reads CSV directly for movie lookups
- Simpler but slower for large datasets
- No database storage needed for movies

**Recommendation**: Use Option 1 for better performance and easier querying.

## Key Design Decisions

1. **Movies from CSV**: Movie catalog is external (CSV), not managed in database
2. **Reviews drive recommendations**: Only reviewed movies influence recommendations
3. **Real-time processing**: Reviews processed immediately via Kafka + PySpark
4. **Sentiment-based ratings**: Text reviews converted to numerical ratings via sentiment analysis
5. **Collaborative filtering**: Recommendations based on similar users' preferences

