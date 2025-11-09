import mysql.connector

def test_application_validation():
    """Test the application-level validation logic we added to the enrollment process"""
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1111',
            database='gaming_platform'
        )
        cursor = conn.cursor()
        
        print("=== Testing Application-Level Gaming ID Validation ===\n")
        
        # Set up test data
        cursor.execute("SELECT id, room_name FROM rooms LIMIT 1")
        room = cursor.fetchone()
        
        cursor.execute("SELECT id, gaming_username FROM user_gaming_ids LIMIT 2")
        gaming_ids = cursor.fetchall()
        
        if not room or not gaming_ids or len(gaming_ids) < 2:
            print("❌ Need at least 1 room and 2 gaming IDs for testing")
            return
            
        room_id, room_name = room
        gaming_id1, gaming_username1 = gaming_ids[0]
        gaming_id2, gaming_username2 = gaming_ids[1]
        
        print(f"Test Setup:")
        print(f"  Room: {room_name} (ID: {room_id})")
        print(f"  Gaming ID 1: {gaming_username1} (ID: {gaming_id1})")
        print(f"  Gaming ID 2: {gaming_username2} (ID: {gaming_id2})")
        print()
        
        # Clean up any existing test enrollments
        cursor.execute("DELETE FROM room_gaming_ids WHERE user_gaming_id IN (%s, %s)", 
                      (gaming_id1, gaming_id2))
        cursor.execute("DELETE FROM room_user_enrollments WHERE room_id = %s", (room_id,))
        conn.commit()
        
        # Create a test enrollment with gaming_id1
        print("🧪 Setting up: Enrolling gaming ID 1 in the room...")
        cursor.execute("""
            INSERT INTO room_user_enrollments 
            (room_id, user_id, total_entry_fee, gaming_ids_count, payment_status, is_active)
            VALUES (%s, 1, 100, 1, 'paid', 1)
        """, (room_id,))
        enrollment_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO room_gaming_ids 
            (room_user_enrollment_id, user_gaming_id, room_id)
            VALUES (%s, %s, %s)
        """, (enrollment_id, gaming_id1, room_id))
        conn.commit()
        
        print(f"✅ Gaming ID {gaming_username1} is now enrolled in {room_name}")
        
        # Test the validation query that we added to the application
        print(f"\n🧪 Testing validation query for gaming IDs: [{gaming_id1}, {gaming_id2}]")
        
        selected_gaming_ids = [str(gaming_id1), str(gaming_id2)]  # Simulate user selection
        gaming_ids_placeholders = ','.join(['%s'] * len(selected_gaming_ids))
        
        query = f"""
            SELECT ug.gaming_username, ug.gaming_platform, u.username
            FROM room_gaming_ids rgi
            JOIN room_user_enrollments rue ON rgi.room_user_enrollment_id = rue.id
            JOIN user_gaming_ids ug ON rgi.user_gaming_id = ug.id
            JOIN users u ON rue.user_id = u.id
            WHERE rue.room_id = %s 
            AND rue.is_active = TRUE 
            AND rgi.user_gaming_id IN ({gaming_ids_placeholders})
        """
        
        cursor.execute(query, [room_id] + [int(gid) for gid in selected_gaming_ids])
        already_enrolled = cursor.fetchall()
        
        if already_enrolled:
            print("✅ Validation correctly detected already enrolled gaming IDs:")
            for enrolled in already_enrolled:
                print(f"  ❌ {enrolled[0]} ({enrolled[1]}) - already enrolled by {enrolled[2]}")
            
            print(f"\n💡 Application would show flash message:")
            enrolled_details = []
            for enrolled in already_enrolled:
                enrolled_details.append(f"{enrolled[0]} ({enrolled[1]}) - already enrolled by {enrolled[2]}")
            print(f"⚠️ Gaming ID(s) already enrolled in this room: {', '.join(enrolled_details)}")
            
        else:
            print("❌ Validation failed to detect enrolled gaming IDs")
        
        # Test with gaming IDs that are NOT enrolled
        print(f"\n🧪 Testing with only gaming ID 2 (not enrolled): [{gaming_id2}]")
        cursor.execute(query, [room_id, gaming_id2])
        not_enrolled = cursor.fetchall()
        
        if not not_enrolled:
            print("✅ Validation correctly allows non-enrolled gaming IDs")
        else:
            print("❌ Validation incorrectly blocked non-enrolled gaming IDs")
        
        # Clean up
        print("\n🧹 Cleaning up test data...")
        cursor.execute("DELETE FROM room_gaming_ids WHERE room_user_enrollment_id = %s", (enrollment_id,))
        cursor.execute("DELETE FROM room_user_enrollments WHERE id = %s", (enrollment_id,))
        conn.commit()
        
        print("\n🎉 Application-level validation test completed!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_application_validation()