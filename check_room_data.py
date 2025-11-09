import mysql.connector

def check_room_data():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1111',
            database='gaming_platform'
        )
        cursor = conn.cursor()
        
        # Check the rooms table structure
        cursor.execute('DESCRIBE rooms')
        columns = cursor.fetchall()
        print('=== ROOMS TABLE STRUCTURE ===')
        for col in columns:
            print(f'{col[0]} - {col[1]} - {col[2]}')
        
        # Check some sample room data
        cursor.execute('SELECT id, room_name, entry_fee FROM rooms LIMIT 3')
        rooms = cursor.fetchall()
        print('\n=== SAMPLE ROOM DATA ===')
        for room in rooms:
            print(f'ID: {room[0]}, Name: {room[1]}, Entry Fee: {room[2]} (type: {type(room[2])})')
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_room_data()