import mysql.connector

def check_room_columns():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1111',
            database='gaming_platform'
        )
        cursor = conn.cursor()
        
        # Check the rooms table structure for team size columns
        cursor.execute('DESCRIBE rooms')
        columns = cursor.fetchall()
        print('=== ROOMS TABLE COLUMNS ===')
        for i, col in enumerate(columns):
            print(f'Index {i}: {col[0]} - {col[1]}')
        
        # Get sample room data to see the team size values
        cursor.execute('SELECT id, room_name, min_team_size, max_team_size, max_gaming_ids_per_user FROM rooms LIMIT 2')
        rooms = cursor.fetchall()
        print('\n=== SAMPLE ROOM DATA ===')
        for room in rooms:
            print(f'Room {room[0]}: {room[1]}')
            print(f'  min_team_size: {room[2]}')
            print(f'  max_team_size: {room[3]}')
            print(f'  max_gaming_ids_per_user: {room[4]}')
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_room_columns()