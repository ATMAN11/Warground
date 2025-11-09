import mysql.connector
import os

def fix_gaming_id_duplicates():
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1111',
            database='gaming_platform'
        )
        cursor = conn.cursor()
        
        print("=== Checking for existing duplicate gaming IDs ===")
        
        # Check for existing duplicates
        cursor.execute("""
            SELECT 
                r.room_name,
                ug.gaming_username,
                ug.gaming_platform,
                COUNT(*) as enrollment_count,
                GROUP_CONCAT(u.username) as users
            FROM room_gaming_ids rgi
            JOIN room_user_enrollments rue ON rgi.room_user_enrollment_id = rue.id
            JOIN user_gaming_ids ug ON rgi.user_gaming_id = ug.id
            JOIN users u ON rue.user_id = u.id
            JOIN rooms r ON rue.room_id = r.id
            WHERE rue.is_active = TRUE
            GROUP BY rue.room_id, rgi.user_gaming_id
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print("⚠️  Found existing duplicates:")
            for dup in duplicates:
                print(f"Room: {dup[0]}, Gaming ID: {dup[1]} ({dup[2]}), Count: {dup[3]}, Users: {dup[4]}")
        else:
            print("✅ No existing duplicate gaming IDs found")
        
        print("\n=== Adding room_id column to room_gaming_ids ===")
        
        # Check if room_id column already exists
        cursor.execute("SHOW COLUMNS FROM room_gaming_ids LIKE 'room_id'")
        room_id_exists = cursor.fetchone()
        
        if not room_id_exists:
            # Add room_id column
            cursor.execute("ALTER TABLE room_gaming_ids ADD COLUMN room_id INT")
            print("✅ Added room_id column")
            
            # Update room_id values
            cursor.execute("""
                UPDATE room_gaming_ids rgi
                JOIN room_user_enrollments rue ON rgi.room_user_enrollment_id = rue.id
                SET rgi.room_id = rue.room_id
            """)
            print("✅ Updated room_id values")
            
            # Add foreign key constraint
            cursor.execute("""
                ALTER TABLE room_gaming_ids 
                ADD CONSTRAINT fk_room_gaming_ids_room 
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            """)
            print("✅ Added foreign key constraint")
        else:
            print("✅ room_id column already exists")
        
        print("\n=== Adding unique constraint ===")
        
        # Check if unique constraint already exists
        cursor.execute("""
            SELECT CONSTRAINT_NAME 
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
            WHERE TABLE_SCHEMA = 'gaming_platform' 
            AND TABLE_NAME = 'room_gaming_ids' 
            AND CONSTRAINT_NAME = 'unique_gaming_id_per_room'
        """)
        constraint_exists = cursor.fetchone()
        
        if not constraint_exists:
            try:
                # Add unique constraint
                cursor.execute("""
                    ALTER TABLE room_gaming_ids 
                    ADD CONSTRAINT unique_gaming_id_per_room 
                    UNIQUE KEY (room_id, user_gaming_id)
                """)
                print("✅ Added unique constraint to prevent duplicate gaming IDs per room")
            except mysql.connector.Error as e:
                print(f"⚠️  Could not add unique constraint due to existing data: {e}")
                print("This likely means there are existing duplicates that need to be cleaned up first")
        else:
            print("✅ Unique constraint already exists")
        
        # Create performance index
        try:
            cursor.execute("CREATE INDEX idx_room_gaming_ids_lookup ON room_gaming_ids (room_id, user_gaming_id)")
            print("✅ Added performance index")
        except mysql.connector.Error as e:
            if "Duplicate key name" in str(e):
                print("✅ Performance index already exists")
            else:
                print(f"⚠️  Could not add index: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 Gaming ID duplicate prevention system setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_gaming_id_duplicates()