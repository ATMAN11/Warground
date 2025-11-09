import mysql.connector

def test_winner_calculation():
    """Test the winner calculation logic directly"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1111',
            database='gaming_platform'
        )
        cursor = conn.cursor()
        
        # Get a room with players
        cursor.execute("""
            SELECT r.*, COUNT(DISTINCT rgi.user_gaming_id) as player_count
            FROM rooms r
            LEFT JOIN room_user_enrollments rue ON r.id = rue.room_id AND rue.payment_status = 'paid'
            LEFT JOIN room_gaming_ids rgi ON rue.id = rgi.room_user_enrollment_id
            GROUP BY r.id
            HAVING player_count > 0
            LIMIT 1
        """)
        room_data = cursor.fetchone()
        
        if room_data:
            room_id = room_data[0]
            room_name = room_data[1]
            entry_fee = room_data[3]  # entry_fee is 4th column (index 3)
            player_count = room_data[-1]  # last column
            
            print(f"=== Testing Room: {room_name} ===")
            print(f"Room ID: {room_id}")
            print(f"Entry Fee: {entry_fee} (type: {type(entry_fee)})")
            print(f"Players: {player_count}")
            
            # Test the calculation logic
            total_players = player_count
            if total_players == 0:
                total_prize_pool = 0
            else:
                entry_fee_float = float(entry_fee) if entry_fee is not None else 0
                total_prize_pool = total_players * entry_fee_float * 0.8
            
            print(f"Prize Pool Calculation: {total_players} * {entry_fee_float} * 0.8 = {total_prize_pool}")
            
            # Test reward calculations
            reward_1st = total_prize_pool * 0.6
            reward_2nd = total_prize_pool * 0.3
            reward_3rd = total_prize_pool * 0.1
            
            print(f"1st Place: {reward_1st}")
            print(f"2nd Place: {reward_2nd}")
            print(f"3rd Place: {reward_3rd}")
            print("✅ All calculations successful!")
            
        else:
            print("No rooms with players found")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_winner_calculation()