#!/usr/bin/env python3

import os
from dotenv import load_dotenv
load_dotenv()

import MySQLdb

try:
    db = MySQLdb.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        passwd=os.getenv('MYSQL_PASSWORD', '1111'),
        db=os.getenv('MYSQL_DB', 'gaming_platform')
    )
    cur = db.cursor()
    
    # Check current room columns
    cur.execute('DESCRIBE rooms')
    columns = cur.fetchall()
    print('=== CURRENT ROOM COLUMNS ===')
    existing_cols = []
    for col in columns:
        print(f'{col[0]} - {col[1]}')
        existing_cols.append(col[0])
    
    # Add is_active column if not exists
    if 'is_active' not in existing_cols:
        cur.execute('ALTER TABLE rooms ADD COLUMN is_active TINYINT(1) DEFAULT 1')
        print('✅ Added is_active column')
    else:
        print('ℹ️ is_active column already exists')
    
    # Create blocked_users table if not exists
    cur.execute('''
        CREATE TABLE IF NOT EXISTS blocked_users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            room_id INT NOT NULL,
            user_id INT NOT NULL,
            blocked_by INT NOT NULL,
            reason VARCHAR(255),
            blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (blocked_by) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_block (room_id, user_id)
        )
    ''')
    print('✅ Created/verified blocked_users table')
    
    # Create blocked_teams table if not exists
    cur.execute('''
        CREATE TABLE IF NOT EXISTS blocked_teams (
            id INT PRIMARY KEY AUTO_INCREMENT,
            room_id INT NOT NULL,
            team_id INT NOT NULL,
            blocked_by INT NOT NULL,
            reason VARCHAR(255),
            blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (blocked_by) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_team_block (room_id, team_id)
        )
    ''')
    print('✅ Created/verified blocked_teams table')
    
    db.commit()
    cur.close()
    db.close()
    print('✅ Database setup completed successfully!')
    
except Exception as e:
    print(f'❌ Error: {e}')