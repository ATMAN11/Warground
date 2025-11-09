#!/usr/bin/env python3
"""
Create new database tables for Gaming IDs functionality without altering existing tables.
This script adds support for multiple gaming IDs per user and room enrollment based on gaming IDs.
"""

import os
from dotenv import load_dotenv
import MySQLdb

# Load environment variables
load_dotenv()

def create_gaming_ids_tables():
    try:
        db = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            passwd=os.getenv('MYSQL_PASSWORD', '1111'),
            db=os.getenv('MYSQL_DB', 'gaming_platform')
        )
        cur = db.cursor()
        
        print('🔄 Creating new tables for Gaming IDs functionality...')
        
        # 1. User Gaming IDs Table - Replaces the need for teams
        print('\n1. Creating user_gaming_ids table...')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user_gaming_ids (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                gaming_platform VARCHAR(50) NOT NULL DEFAULT 'PUBG',
                gaming_username VARCHAR(100) NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                is_primary BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_platform (user_id, gaming_platform),
                INDEX idx_user_primary (user_id, is_primary)
            )
        ''')
        print('✅ user_gaming_ids table created successfully')
        
        # 2. Room User Enrollments Table - Direct enrollment with gaming IDs
        print('\n2. Creating room_user_enrollments table...')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS room_user_enrollments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_id INT NOT NULL,
                user_id INT NOT NULL,
                total_entry_fee INT NOT NULL,
                gaming_ids_count INT NOT NULL DEFAULT 1,
                payment_status ENUM('pending', 'paid', 'failed') DEFAULT 'pending',
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE KEY unique_room_user (room_id, user_id),
                INDEX idx_room_status (room_id, payment_status),
                INDEX idx_user_active (user_id, is_active)
            )
        ''')
        print('✅ room_user_enrollments table created successfully')
        
        # 3. Room Gaming IDs Table - Links specific gaming IDs to room enrollments
        print('\n3. Creating room_gaming_ids table...')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS room_gaming_ids (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_user_enrollment_id INT NOT NULL,
                user_gaming_id INT NOT NULL,
                selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_playing BOOLEAN DEFAULT TRUE,
                kills_count INT DEFAULT 0,
                reward_earned DECIMAL(10,2) DEFAULT 0.00,
                status ENUM('enrolled', 'playing', 'completed', 'disqualified') DEFAULT 'enrolled',
                FOREIGN KEY (room_user_enrollment_id) REFERENCES room_user_enrollments(id) ON DELETE CASCADE,
                FOREIGN KEY (user_gaming_id) REFERENCES user_gaming_ids(id) ON DELETE CASCADE,
                UNIQUE KEY unique_enrollment_gaming_id (room_user_enrollment_id, user_gaming_id),
                INDEX idx_room_enrollment (room_user_enrollment_id),
                INDEX idx_kills_rewards (kills_count, reward_earned)
            )
        ''')
        print('✅ room_gaming_ids table created successfully')
        
        # 4. Gaming ID Statistics Table - Track performance across rooms
        print('\n4. Creating user_gaming_id_stats table...')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user_gaming_id_stats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_gaming_id INT NOT NULL,
                total_rooms_joined INT DEFAULT 0,
                total_kills INT DEFAULT 0,
                total_rewards_earned DECIMAL(10,2) DEFAULT 0.00,
                avg_kills_per_room DECIMAL(5,2) DEFAULT 0.00,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_gaming_id) REFERENCES user_gaming_ids(id) ON DELETE CASCADE,
                INDEX idx_gaming_id (user_gaming_id),
                INDEX idx_performance (total_kills, total_rewards_earned)
            )
        ''')
        print('✅ user_gaming_id_stats table created successfully')
        
        db.commit()
        
        # Show table structures
        print('\n📊 New table structures created:')
        tables = ['user_gaming_ids', 'room_user_enrollments', 'room_gaming_ids', 'user_gaming_id_stats']
        
        for table in tables:
            print(f'\n--- {table.upper()} ---')
            cur.execute(f'DESCRIBE {table}')
            columns = cur.fetchall()
            for col in columns:
                print(f'  {col[0]}: {col[1]} {col[2]} {col[3] if col[3] else ""}')
        
        # Migrate existing data if needed
        print('\n🔄 Checking for existing data migration...')
        
        # Check if we have existing pubg_usernames to migrate
        cur.execute('SELECT COUNT(*) FROM pubg_usernames')
        existing_pubg_count = cur.fetchone()[0]
        
        if existing_pubg_count > 0:
            print(f'Found {existing_pubg_count} existing PUBG usernames to migrate...')
            
            # Migrate existing pubg_usernames to user_gaming_ids
            cur.execute('''
                INSERT INTO user_gaming_ids (user_id, gaming_platform, gaming_username, display_name, is_primary)
                SELECT 
                    user_id, 
                    'PUBG' as gaming_platform,
                    pubg_username as gaming_username,
                    pubg_username as display_name,
                    is_primary
                FROM pubg_usernames
                WHERE NOT EXISTS (
                    SELECT 1 FROM user_gaming_ids 
                    WHERE user_gaming_ids.user_id = pubg_usernames.user_id 
                    AND user_gaming_ids.gaming_username = pubg_usernames.pubg_username
                )
            ''')
            migrated = cur.rowcount
            print(f'✅ Migrated {migrated} PUBG usernames to new gaming IDs system')
            
            # Set primary gaming ID for users who don't have one
            cur.execute('''
                UPDATE user_gaming_ids 
                SET is_primary = TRUE 
                WHERE id IN (
                    SELECT * FROM (
                        SELECT MIN(id) 
                        FROM user_gaming_ids 
                        WHERE user_id NOT IN (
                            SELECT user_id FROM user_gaming_ids WHERE is_primary = TRUE
                        )
                        GROUP BY user_id
                    ) as subquery
                )
            ''')
            
            db.commit()
        
        cur.close()
        db.close()
        
        print('\n🎉 Gaming IDs schema creation completed successfully!')
        print('\n📋 Next Steps:')
        print('1. Update application routes to use new gaming IDs system')
        print('2. Create UI for managing gaming IDs')
        print('3. Update room enrollment logic')
        print('4. Test the new functionality')
        
    except Exception as e:
        print(f'❌ Error creating schema: {e}')
        if 'db' in locals():
            db.rollback()

if __name__ == '__main__':
    create_gaming_ids_tables()