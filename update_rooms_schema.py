import mysql.connector

try:
    # Connect to database
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        password='1111',
        database='gaming_platform'
    )
    
    cursor = db.cursor()
    
    # Add min_players_to_start column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE rooms ADD COLUMN min_players_to_start INT DEFAULT 2 AFTER max_players")
        print("✅ Added min_players_to_start column to rooms table")
    except mysql.connector.Error as e:
        if "Duplicate column name" in str(e):
            print("ℹ️ min_players_to_start column already exists")
        else:
            print(f"❌ Error adding column: {e}")
    
    # Add kill reward columns if they don't exist
    columns_to_add = [
        ("kill_rewards_enabled", "BOOLEAN DEFAULT FALSE AFTER status"),
        ("min_kills_required", "INT DEFAULT 0 AFTER kill_rewards_enabled"),
        ("reward_per_kill", "DECIMAL(10,2) DEFAULT 0.00 AFTER min_kills_required")
    ]
    
    for column_name, column_def in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE rooms ADD COLUMN {column_name} {column_def}")
            print(f"✅ Added {column_name} column to rooms table")
        except mysql.connector.Error as e:
            if "Duplicate column name" in str(e):
                print(f"ℹ️ {column_name} column already exists")
            else:
                print(f"❌ Error adding {column_name} column: {e}")
    
    db.commit()
    print("\n🎯 Database schema updated successfully!")

except mysql.connector.Error as err:
    print(f"❌ Database Error: {err}")
finally:
    if 'db' in locals():
        db.close()