-- Run once on existing databases that predate JWT + password_hash.
-- Usage: mysql -h ... -P 3307 -u ... -p cinestream < migrate_users_password_jwt.sql

USE cinestream;

-- Add column if your users table was created without it
SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'password_hash'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NULL AFTER email',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Default password for seeded user: testpass123 (bcrypt)
UPDATE users
SET password_hash = '$2b$12$tqQqKmF/0jYb4UpFziOiguwtsegOIuPtVEWBctiR8BbdHVNIfLrI2'
WHERE user_id = 1 AND (password_hash IS NULL OR password_hash = '');

-- Optional: set a temporary password for other legacy rows (adjust as needed)
-- UPDATE users SET password_hash = '...' WHERE password_hash IS NULL;
