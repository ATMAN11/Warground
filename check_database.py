#!/usr/bin/env python3

import MySQLdb
import sys

# Database configuration
config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1111',  # Update with your MySQL password
    'database': 'gaming_platform'
}

def check_and_fix_database():
    try:
        # Connect to MySQL
        connection = MySQLdb.connect(**config)
        cursor = connection.cursor()
        
        print("Connected to MySQL database")
        
        # Check what tables exist
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        existing_tables = [table[0] for table in tables]
        
        print(f"Existing tables: {existing_tables}")
        
        # Check if user_teams table exists and its structure
        if 'user_teams' in existing_tables:
            print("\nuser_teams table exists. Checking structure...")
            cursor.execute("DESCRIBE user_teams")
            columns = cursor.fetchall()
            column_names = [col[0] for col in columns]
            print(f"Columns in user_teams: {column_names}")
            
            # Check if team_size column exists
            if 'team_size' not in column_names:
                print("Adding missing team_size column...")
                cursor.execute("ALTER TABLE user_teams ADD COLUMN team_size INT DEFAULT 1")
                connection.commit()
                print("✓ Added team_size column")
        else:
            print("Creating user_teams table...")
            cursor.execute("""
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
                )
            """)
            connection.commit()
            print("✓ Created user_teams table")
        
        # Check user_team_members table
        if 'user_team_members' not in existing_tables:
            print("Creating user_team_members table...")
            cursor.execute("""
                CREATE TABLE user_team_members (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_team_id INT NOT NULL,
                    username VARCHAR(50) NOT NULL,
                    gaming_id VARCHAR(100),
                    email VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_team_id) REFERENCES user_teams(id) ON DELETE CASCADE
                )
            """)
            connection.commit()
            print("✓ Created user_team_members table")
        
        # Check room_team_enrollments table  
        if 'room_team_enrollments' not in existing_tables:
            print("Creating room_team_enrollments table...")
            cursor.execute("""
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
                )
            """)
            connection.commit()
            print("✓ Created room_team_enrollments table")
        
        # Final check - show all tables
        cursor.execute("SHOW TABLES")
        final_tables = cursor.fetchall()
        print(f"\nAll tables after update: {[table[0] for table in final_tables]}")
        
        cursor.close()
        connection.close()
        print("\n✅ Database check and update completed successfully!")
        
    except MySQLdb.Error as e:
        print(f"❌ MySQL Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_and_fix_database()