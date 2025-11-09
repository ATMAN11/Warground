-- Add missing columns to existing rooms table
ALTER TABLE rooms 
ADD COLUMN IF NOT EXISTS event_timing DATETIME DEFAULT NULL,
ADD COLUMN IF NOT EXISTS is_multiplayer BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS min_team_size INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS max_team_size INT DEFAULT 4;

-- Create teams table if it doesn't exist
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

-- Create team_members table if it doesn't exist
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