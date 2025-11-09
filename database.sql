CREATE DATABASE IF NOT EXISTS gaming_platform;
USE gaming_platform;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    gpay_number VARCHAR(20) NOT NULL,
    coins INT DEFAULT 0,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PUBG Usernames table
CREATE TABLE pubg_usernames (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pubg_username VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Rooms table
CREATE TABLE rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_name VARCHAR(100) NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    entry_fee INT NOT NULL,
    prize_pool INT NOT NULL,
    max_players INT NOT NULL,
    min_players_to_start INT DEFAULT 2,
    room_id_game VARCHAR(50) NOT NULL,
    room_password VARCHAR(50) NOT NULL,
    event_timing DATETIME NOT NULL,
    is_multiplayer BOOLEAN DEFAULT TRUE,
    min_team_size INT DEFAULT 1,
    max_team_size INT DEFAULT 4,
    status VARCHAR(20) DEFAULT 'open',
    kill_rewards_enabled BOOLEAN DEFAULT FALSE,
    min_kills_required INT DEFAULT 0,
    reward_per_kill DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teams table
CREATE TABLE teams (
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

-- Team members table
CREATE TABLE team_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    team_id INT NOT NULL,
    user_id INT NOT NULL,
    pubg_username_id INT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pubg_username_id) REFERENCES pubg_usernames(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_room (team_id, user_id)
);

-- Enrollments table
CREATE TABLE enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    pubg_username_id INT NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'paid',
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pubg_username_id) REFERENCES pubg_usernames(id) ON DELETE CASCADE
);

-- Withdrawals table
CREATE TABLE withdrawals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount INT NOT NULL,
    gpay_number VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    payment_screenshot VARCHAR(255),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Transactions table
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type VARCHAR(20) NOT NULL,
    amount INT NOT NULL,
    payment_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Persistent team management tables
CREATE TABLE user_teams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    team_email VARCHAR(100),
    team_size INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE user_team_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_team_id INT NOT NULL,
    member_username VARCHAR(50) NOT NULL,
    gaming_id VARCHAR(100),
    email VARCHAR(100),
    is_leader BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_team_id) REFERENCES user_teams(id) ON DELETE CASCADE
);

CREATE TABLE room_team_enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    user_team_id INT NOT NULL,
    total_entry_fee INT NOT NULL,
    payment_status ENUM('pending', 'paid', 'failed') DEFAULT 'pending',
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_team_id) REFERENCES user_teams(id) ON DELETE CASCADE,
    UNIQUE KEY unique_room_team (room_id, user_team_id)
);

-- Insert default admin user (username: admin, password: admin123)
INSERT INTO users (username, password, gpay_number, is_admin, coins) 
VALUES ('admin', 'admin123', '9999999999', TRUE, 0);