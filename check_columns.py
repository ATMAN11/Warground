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
    
    # Check user_team_members table structure
    print("=== user_team_members table structure ===")
    cursor.execute("DESCRIBE user_team_members")
    columns = cursor.fetchall()
    
    for column in columns:
        print(f"Column: {column[0]}, Type: {column[1]}, Null: {column[2]}, Key: {column[3]}, Default: {column[4]}, Extra: {column[5]}")
    
    # Check if table exists and has data
    print("\n=== user_team_members table data ===")
    cursor.execute("SELECT COUNT(*) FROM user_team_members")
    count = cursor.fetchone()[0]
    print(f"Number of records: {count}")
    
    # Check user_teams table structure  
    print("\n=== user_teams table structure ===")
    cursor.execute("DESCRIBE user_teams")
    columns = cursor.fetchall()
    
    for column in columns:
        print(f"Column: {column[0]}, Type: {column[1]}, Null: {column[2]}, Key: {column[3]}, Default: {column[4]}, Extra: {column[5]}")
    
    # Check room_team_enrollments table structure
    print("\n=== room_team_enrollments table structure ===")
    cursor.execute("DESCRIBE room_team_enrollments")
    columns = cursor.fetchall()
    
    for column in columns:
        print(f"Column: {column[0]}, Type: {column[1]}, Null: {column[2]}, Key: {column[3]}, Default: {column[4]}, Extra: {column[5]}")

except mysql.connector.Error as err:
    print(f"Error: {err}")
finally:
    if 'db' in locals():
        db.close()