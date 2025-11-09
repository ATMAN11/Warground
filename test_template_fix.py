import mysql.connector

def test_template_calculation():
    """Test the template calculation that was causing the error"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1111',
            database='gaming_platform'
        )
        cursor = conn.cursor()
        
        # Get a room and simulate the template calculation
        cursor.execute("SELECT * FROM rooms LIMIT 1")
        room = cursor.fetchone()
        
        if room:
            print(f"=== Testing Template Calculation ===")
            print(f"Room data: {room[:5]}...")  # Show first 5 columns
            print(f"room[0] (id): {room[0]}")
            print(f"room[1] (room_name): {room[1]}")
            print(f"room[2] (game_type): {room[2]} (type: {type(room[2])})")
            print(f"room[3] (entry_fee): {room[3]} (type: {type(room[3])})")
            
            # Simulate players count
            players_count = 2
            
            print(f"\n=== OLD CALCULATION (BROKEN) ===")
            try:
                # This was the broken calculation: room[2] * 0.8
                old_result = players_count * room[2] * 0.8
                print(f"players_count * room[2] * 0.8 = {players_count} * {room[2]} * 0.8 = {old_result}")
                print("❌ This should have failed!")
            except Exception as e:
                print(f"✅ Correctly failed: {e}")
            
            print(f"\n=== NEW CALCULATION (FIXED) ===")
            try:
                # This is the fixed calculation: room[3] * 0.8
                new_result = players_count * room[3] * 0.8
                print(f"players_count * room[3] * 0.8 = {players_count} * {room[3]} * 0.8 = {new_result}")
                print("✅ Fixed calculation works correctly!")
            except Exception as e:
                print(f"❌ Fixed calculation failed: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Test error: {e}")

if __name__ == "__main__":
    test_template_calculation()