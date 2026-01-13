// CineStream MongoDB Initialization Script

// Switch to the logs database
db = db.getSiblingDB('cinestream_logs');

// Create collections
db.createCollection('review_logs');
db.createCollection('streaming_logs');
db.createCollection('processing_errors');

// Create indexes for review_logs
db.review_logs.createIndex({ user_id: 1, timestamp: -1 });
db.review_logs.createIndex({ movie_id: 1 });
db.review_logs.createIndex({ timestamp: -1 });

// Create indexes for streaming_logs
db.streaming_logs.createIndex({ timestamp: -1 });
db.streaming_logs.createIndex({ batch_id: 1 });

// Create indexes for processing_errors
db.processing_errors.createIndex({ timestamp: -1 });
db.processing_errors.createIndex({ error_type: 1 });

// Create a user for the application (optional, for security)
db.createUser({
    user: 'cinestream_app',
    pwd: 'cinestream_app_password',
    roles: [
        {
            role: 'readWrite',
            db: 'cinestream_logs'
        }
    ]
});

print('MongoDB initialization complete!');

