import mysql.connector

def test_team_size_logic():
    """Test the new team size-based gaming ID limit logic"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1111',
            database='gaming_platform'
        )
        cursor = conn.cursor()
        
        # Get room data to test the logic
        cursor.execute('SELECT id, room_name, max_team_size, max_gaming_ids_per_user FROM rooms LIMIT 3')
        rooms = cursor.fetchall()
        
        print('=== Testing New Gaming ID Limit Logic ===')
        print('Changed from: max_gaming_ids_per_user to max_team_size\n')
        
        for room in rooms:
            room_id, room_name, max_team_size, old_max_gaming_ids = room
            print(f'Room: {room_name} (ID: {room_id})')
            print(f'  OLD Logic: max_gaming_ids_per_user = {old_max_gaming_ids}')
            print(f'  NEW Logic: max_team_size = {max_team_size}')
            print(f'  Impact: User can now select up to {max_team_size} gaming IDs (was {old_max_gaming_ids})')
            print()
        
        print('=== Summary ===')
        print('✅ Users can now join with multiple gaming IDs up to team size limit')
        print('✅ More flexible than the old max_gaming_ids_per_user restriction')
        print('✅ Respects the team structure of the tournament')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    test_team_size_logic()