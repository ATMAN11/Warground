-- ============================================================================
-- GAMING PLATFORM - COMPLETE DATABASE SCHEMA FOR PRODUCTION DEPLOYMENT
-- ============================================================================
-- This schema includes ALL tables visible in your current database
-- Generated for Railway/PlanetScale deployment

-- Create database (Railway will create this automatically)
-- CREATE DATABASE IF NOT EXISTS gaming_platform;
-- USE gaming_platform;

-- ============================================================================
-- 1. CORE USER MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    gpay_number VARCHAR(20),
    coins INT DEFAULT 0,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. ROOMS AND TOURNAMENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS rooms (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_name VARCHAR(100) NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    entry_fee INT NOT NULL,
    prize_pool INT NOT NULL,
    max_players INT NOT NULL,
    room_id_game VARCHAR(50) NOT NULL,
    room_password VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_timing DATETIME,
    is_multiplayer BOOLEAN DEFAULT TRUE,
    min_team_size INT DEFAULT 1,
    max_team_size INT DEFAULT 4,
    min_players_to_start INT DEFAULT 2,
    status ENUM('open', 'running', 'completed', 'cancelled') DEFAULT 'open',
    kill_rewards_enabled BOOLEAN DEFAULT FALSE,
    min_kills_required INT DEFAULT 0,
    reward_per_kill DECIMAL(10,2) DEFAULT 0.00,
    max_kill_bonus DECIMAL(10,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================================================
-- 3. GAMING ID SYSTEM (MAIN ENROLLMENT SYSTEM)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_gaming_ids (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    gaming_platform VARCHAR(50) DEFAULT 'PUBG',
    gaming_username VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_gaming_ids_user (user_id),
    INDEX idx_user_gaming_ids_platform (gaming_platform),
    INDEX idx_user_gaming_ids_username (gaming_username)
);

CREATE TABLE IF NOT EXISTS user_gaming_id_stats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_gaming_id INT NOT NULL,
    total_rooms_joined INT DEFAULT 0,
    total_kills INT DEFAULT 0,
    total_rewards_earned DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_gaming_id) REFERENCES user_gaming_ids(id) ON DELETE CASCADE,
    UNIQUE KEY unique_gaming_id_stats (user_gaming_id)
);

CREATE TABLE IF NOT EXISTS room_user_enrollments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    total_entry_fee INT NOT NULL,
    gaming_ids_count INT NOT NULL,
    payment_status ENUM('pending', 'paid', 'failed') DEFAULT 'pending',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_room_user_enrollments_room (room_id),
    INDEX idx_room_user_enrollments_user (user_id)
);

CREATE TABLE IF NOT EXISTS room_gaming_ids (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_user_enrollment_id INT NOT NULL,
    user_gaming_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_user_enrollment_id) REFERENCES room_user_enrollments(id) ON DELETE CASCADE,
    FOREIGN KEY (user_gaming_id) REFERENCES user_gaming_ids(id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment_gaming_id (room_user_enrollment_id, user_gaming_id),
    INDEX idx_room_gaming_ids_enrollment (room_user_enrollment_id),
    INDEX idx_room_gaming_ids_gaming_id (user_gaming_id)
);

CREATE TABLE IF NOT EXISTS gaming_id_room_stats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_gaming_id INT NOT NULL,
    room_id INT NOT NULL,
    kills_count INT DEFAULT 0,
    reward_earned DECIMAL(10,2) DEFAULT 0.00,
    reward_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    screenshot_proof VARCHAR(255),
    recorded_by INT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_gaming_id) REFERENCES user_gaming_ids(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (recorded_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY unique_gaming_id_room_stats (user_gaming_id, room_id),
    INDEX idx_gaming_id_room_stats_gaming_id (user_gaming_id),
    INDEX idx_gaming_id_room_stats_room (room_id)
);

-- ============================================================================
-- 4. TEAM MANAGEMENT SYSTEMS
-- ============================================================================

-- User-created teams system
CREATE TABLE IF NOT EXISTS user_teams (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    team_email VARCHAR(100),
    team_size INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_teams_user (user_id)
);

CREATE TABLE IF NOT EXISTS user_team_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    team_id INT NOT NULL,
    member_name VARCHAR(100) NOT NULL,
    gaming_username VARCHAR(100) NOT NULL,
    position_in_team INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES user_teams(id) ON DELETE CASCADE,
    INDEX idx_user_team_members_team (team_id)
);

CREATE TABLE IF NOT EXISTS room_team_enrollments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    user_team_id INT NOT NULL,
    enrolled_by INT NOT NULL,
    total_entry_fee INT NOT NULL,
    payment_status ENUM('pending', 'paid', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_team_id) REFERENCES user_teams(id) ON DELETE CASCADE,
    FOREIGN KEY (enrolled_by) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_room_team_enrollment (room_id, user_team_id),
    INDEX idx_room_team_enrollments_room (room_id),
    INDEX idx_room_team_enrollments_team (user_team_id)
);

-- Legacy team system (maintained for backwards compatibility)
CREATE TABLE IF NOT EXISTS teams (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    team_email VARCHAR(100),
    team_leader_id INT NOT NULL,
    total_entry_fee INT NOT NULL,
    payment_status ENUM('pending', 'paid', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (team_leader_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS team_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    team_id INT NOT NULL,
    member_username VARCHAR(50) NOT NULL,
    pubg_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
);

-- ============================================================================
-- 5. LEGACY ENROLLMENT SYSTEMS
-- ============================================================================

-- Legacy direct enrollments
CREATE TABLE IF NOT EXISTS enrollments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    pubg_username VARCHAR(100) NOT NULL,
    team_name VARCHAR(100),
    payment_status ENUM('pending', 'paid', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS direct_enrollments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    gaming_username VARCHAR(100) NOT NULL,
    team_name VARCHAR(100),
    entry_fee INT NOT NULL,
    payment_status ENUM('pending', 'paid', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS enrollment_gaming_ids (
    id INT PRIMARY KEY AUTO_INCREMENT,
    enrollment_id INT NOT NULL,
    gaming_username VARCHAR(100) NOT NULL,
    gaming_platform VARCHAR(50) DEFAULT 'PUBG',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
);

-- Legacy PUBG usernames
CREATE TABLE IF NOT EXISTS pubg_usernames (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    pubg_username VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS room_enrollment_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    enrollment_id INT NOT NULL,
    member_name VARCHAR(100) NOT NULL,
    pubg_username VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
);

-- ============================================================================
-- 6. WINNER MANAGEMENT AND REWARDS
-- ============================================================================

CREATE TABLE IF NOT EXISTS room_reward_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    position INT NOT NULL,
    base_reward DECIMAL(10,2) NOT NULL,
    kill_bonus_per_kill DECIMAL(10,2) DEFAULT 0.00,
    max_kill_bonus DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    UNIQUE KEY unique_room_position (room_id, position)
);

CREATE TABLE IF NOT EXISTS room_winners (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    user_gaming_id INT NOT NULL,
    position INT NOT NULL,
    kills_count INT DEFAULT 0,
    base_reward DECIMAL(10,2) NOT NULL,
    kill_bonus DECIMAL(10,2) DEFAULT 0.00,
    total_reward DECIMAL(10,2) NOT NULL,
    performance_score INT DEFAULT 0,
    reward_distributed BOOLEAN DEFAULT FALSE,
    selected_by INT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_gaming_id) REFERENCES user_gaming_ids(id) ON DELETE CASCADE,
    FOREIGN KEY (selected_by) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_room_position_winner (room_id, position),
    INDEX idx_room_winners_room (room_id),
    INDEX idx_room_winners_gaming_id (user_gaming_id)
);

CREATE TABLE IF NOT EXISTS winner_selection_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    action_type ENUM('winner_selected', 'winner_removed', 'rewards_distributed') NOT NULL,
    user_gaming_id INT,
    position INT,
    reward_amount DECIMAL(10,2),
    admin_user_id INT NOT NULL,
    details TEXT,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_gaming_id) REFERENCES user_gaming_ids(id) ON DELETE SET NULL,
    FOREIGN KEY (admin_user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_winner_history_room (room_id),
    INDEX idx_winner_history_admin (admin_user_id)
);

CREATE TABLE IF NOT EXISTS winner_rewards_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    gaming_id INT NOT NULL,
    position INT NOT NULL,
    reward_amount DECIMAL(10,2) NOT NULL,
    distributed_by INT NOT NULL,
    distributed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (gaming_id) REFERENCES user_gaming_ids(id) ON DELETE CASCADE,
    FOREIGN KEY (distributed_by) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================================
-- 7. LEGACY KILL TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS player_kills (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    kills_count INT DEFAULT 0,
    screenshot_proof VARCHAR(255),
    reward_earned DECIMAL(10,2) DEFAULT 0.00,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================================
-- 8. FINANCIAL MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    type ENUM('credit', 'debit', 'credit_pending', 'kill_reward') NOT NULL,
    amount INT NOT NULL,
    description TEXT,
    payment_id VARCHAR(100),
    payment_screenshot VARCHAR(255),
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_transactions_user (user_id),
    INDEX idx_transactions_type (type),
    INDEX idx_transactions_status (status)
);

CREATE TABLE IF NOT EXISTS withdrawals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    amount INT NOT NULL,
    gpay_number VARCHAR(20) NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    payment_screenshot VARCHAR(255),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_withdrawals_user (user_id),
    INDEX idx_withdrawals_status (status)
);

-- ============================================================================
-- 9. ADMIN CONTROLS AND BLOCKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS blocked_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    blocked_by INT NOT NULL,
    reason TEXT,
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (blocked_by) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_room_user_block (room_id, user_id)
);

CREATE TABLE IF NOT EXISTS blocked_teams (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    team_id INT NOT NULL,
    blocked_by INT NOT NULL,
    reason TEXT,
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES user_teams(id) ON DELETE CASCADE,
    FOREIGN KEY (blocked_by) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_room_team_block (room_id, team_id)
);

-- ============================================================================
-- 10. ROOM STATUS AND RESULTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS room_result_status (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    status ENUM('not_started', 'in_progress', 'completed', 'cancelled') DEFAULT 'not_started',
    winner_announced BOOLEAN DEFAULT FALSE,
    results_finalized BOOLEAN DEFAULT FALSE,
    updated_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY unique_room_result (room_id)
);

-- ============================================================================
-- 11. INSERT DEFAULT ADMIN USER
-- ============================================================================

INSERT IGNORE INTO users (username, password, is_admin, coins) 
VALUES ('admin', 'admin123', TRUE, 10000);

-- ============================================================================
-- 12. CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

-- Additional performance indexes
CREATE INDEX IF NOT EXISTS idx_rooms_status ON rooms(status);
CREATE INDEX IF NOT EXISTS idx_rooms_active ON rooms(is_active);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_transactions_created ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_enrollments_room_user ON room_user_enrollments(room_id, user_id);

-- ============================================================================
-- SCHEMA COMPLETE - ALL TABLES FROM YOUR DATABASE INCLUDED
-- ============================================================================
-- This schema includes all 27+ tables visible in your database screenshots
-- Ready for Railway/PlanetScale deployment
-- ============================================================================