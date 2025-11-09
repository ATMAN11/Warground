# Database Update Script - Simple Version
# Run this in MySQL Workbench or your preferred MySQL client

USE gaming_platform;

# Add missing columns to existing rooms table
# Note: These will give errors if columns already exist, but that's okay

ALTER TABLE rooms ADD COLUMN event_timing DATETIME DEFAULT NULL;
ALTER TABLE rooms ADD COLUMN is_multiplayer BOOLEAN DEFAULT TRUE;
ALTER TABLE rooms ADD COLUMN min_team_size INT DEFAULT 1;
ALTER TABLE rooms ADD COLUMN max_team_size INT DEFAULT 4;

# Add kill reward system columns
ALTER TABLE rooms ADD COLUMN enable_kill_rewards BOOLEAN DEFAULT FALSE;
ALTER TABLE rooms ADD COLUMN min_kills_required INT DEFAULT 0;
ALTER TABLE rooms ADD COLUMN reward_per_kill DECIMAL(10,2) DEFAULT 0.00;

# Create teams table if it doesn't exist
CREATE TABLE IF NOT EXISTS teams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    team_email VARCHAR(100) NOT NULL,
    team_leader_id INT NOT NULL,
    total_entry_fee INT NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (team_leader_id) REFERENCES users(id) ON DELETE CASCADE
);

# Create team_members table if it doesn't exist
CREATE TABLE IF NOT EXISTS team_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    team_id INT NOT NULL,
    user_id INT NOT NULL,
    pubg_username_id INT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pubg_username_id) REFERENCES pubg_usernames(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_team (team_id, user_id)
);

# Create kill tracking table for individual player performance
CREATE TABLE IF NOT EXISTS player_kills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    team_id INT NOT NULL,
    user_id INT NOT NULL,
    kills_count INT DEFAULT 0,
    reward_earned DECIMAL(10,2) DEFAULT 0.00,
    reward_status VARCHAR(20) DEFAULT 'pending',
    screenshot_proof VARCHAR(255),
    recorded_by INT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recorded_by) REFERENCES users(id),
    UNIQUE KEY unique_player_room (room_id, user_id)
);

# Create persistent user teams table
CREATE TABLE IF NOT EXISTS user_teams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    team_email VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_team_name (user_id, team_name)
);

# Create persistent team members table
CREATE TABLE IF NOT EXISTS user_team_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_team_id INT NOT NULL,
    member_username VARCHAR(50) NOT NULL,
    gaming_id VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    is_leader BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_team_id) REFERENCES user_teams(id) ON DELETE CASCADE,
    UNIQUE KEY unique_team_member (user_team_id, member_username)
);

# Create room enrollments using existing teams
CREATE TABLE IF NOT EXISTS room_team_enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    user_team_id INT NOT NULL,
    enrolled_by INT NOT NULL,
    total_entry_fee INT NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'paid',
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_team_id) REFERENCES user_teams(id) ON DELETE CASCADE,
    FOREIGN KEY (enrolled_by) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_room_team (room_id, user_team_id)
);