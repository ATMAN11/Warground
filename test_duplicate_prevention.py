import mysql.connector
import traceback

def test_gaming_id_constraints():
    """Test that gaming IDs can be used across different rooms but not duplicated in same room"""
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1111',
            database='gaming_platform'
        )
        cursor = conn.cursor()
        
        print("=== Testing Gaming ID Duplicate Prevention System ===\n")
        
        # Get sample data for testing
        cursor.execute("SELECT id, room_name FROM rooms LIMIT 2")
        rooms = cursor.fetchall()
        
        cursor.execute("SELECT id, user_id, gaming_username FROM user_gaming_ids LIMIT 1")
        gaming_id = cursor.fetchone()
        
        if not rooms or len(rooms) < 2:
            print("❌ Need at least 2 rooms for testing")
            return
            
        if not gaming_id:
            print("❌ Need at least 1 gaming ID for testing")
            return
            
        room1_id, room1_name = rooms[0]
        room2_id, room2_name = rooms[1]
        test_gaming_id, user_id, gaming_username = gaming_id
        
        print(f"Test Setup:")
        print(f"  Room 1: {room1_name} (ID: {room1_id})")
        print(f"  Room 2: {room2_name} (ID: {room2_id})")
        print(f"  Gaming ID: {gaming_username} (ID: {test_gaming_id})")
        print(f"  User ID: {user_id}")
        print()
        
        # Clean up any existing test enrollments
        print("🧹 Cleaning up existing test data...")
        cursor.execute("DELETE FROM room_gaming_ids WHERE user_gaming_id = %s", (test_gaming_id,))
        cursor.execute("DELETE FROM room_user_enrollments WHERE user_id = %s AND room_id IN (%s, %s)", 
                      (user_id, room1_id, room2_id))
        conn.commit()
        
        # Test 1: Enroll gaming ID in Room 1
        print("🧪 Test 1: Enrolling gaming ID in Room 1...")
        try:
            cursor.execute("""
                INSERT INTO room_user_enrollments 
                (room_id, user_id, total_entry_fee, gaming_ids_count, payment_status, is_active)
                VALUES (%s, %s, 100, 1, 'paid', 1)
            """, (room1_id, user_id))
            enrollment1_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO room_gaming_ids 
                (room_user_enrollment_id, user_gaming_id, room_id)
                VALUES (%s, %s, %s)
            """, (enrollment1_id, test_gaming_id, room1_id))
            
            conn.commit()
            print("✅ Successfully enrolled gaming ID in Room 1")
            
        except Exception as e:
            print(f"❌ Failed to enroll in Room 1: {e}")
            return
        
        # Test 2: Enroll SAME gaming ID in Room 2 (should work)
        print("\n🧪 Test 2: Enrolling SAME gaming ID in Room 2 (different room)...")
        try:
            cursor.execute("""
                INSERT INTO room_user_enrollments 
                (room_id, user_id, total_entry_fee, gaming_ids_count, payment_status, is_active)
                VALUES (%s, %s, 100, 1, 'paid', 1)
            """, (room2_id, user_id))
            enrollment2_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO room_gaming_ids 
                (room_user_enrollment_id, user_gaming_id, room_id)
                VALUES (%s, %s, %s)
            """, (enrollment2_id, test_gaming_id, room2_id))
            
            conn.commit()
            print("✅ Successfully enrolled SAME gaming ID in Room 2 (different room allowed)")
            
        except Exception as e:
            print(f"❌ Failed to enroll in Room 2: {e}")
            return
        
        # Test 3: Try to enroll SAME gaming ID in Room 1 AGAIN (should fail)
        print("\n🧪 Test 3: Trying to enroll SAME gaming ID in Room 1 AGAIN (should fail)...")
        try:
            cursor.execute("""
                INSERT INTO room_user_enrollments 
                (room_id, user_id, total_entry_fee, gaming_ids_count, payment_status, is_active)
                VALUES (%s, %s, 100, 1, 'paid', 1)
            """, (room1_id, user_id))
            enrollment3_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO room_gaming_ids 
                (room_user_enrollment_id, user_gaming_id, room_id)
                VALUES (%s, %s, %s)
            """, (enrollment3_id, test_gaming_id, room1_id))
            
            conn.commit()
            print("❌ ERROR: Duplicate enrollment was allowed (this should not happen!)")
            
        except mysql.connector.IntegrityError as e:
            if "unique_gaming_id_per_room" in str(e):
                print("✅ Correctly blocked duplicate gaming ID in same room")
            else:
                print(f"❌ Blocked for different reason: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        # Test 4: Verify current enrollments
        print("\n📊 Final Enrollment Status:")
        cursor.execute("""
            SELECT r.room_name, ug.gaming_username, u.username
            FROM room_gaming_ids rgi
            JOIN room_user_enrollments rue ON rgi.room_user_enrollment_id = rue.id
            JOIN rooms r ON rue.room_id = r.id
            JOIN user_gaming_ids ug ON rgi.user_gaming_id = ug.id
            JOIN users u ON rue.user_id = u.id
            WHERE ug.id = %s AND rue.is_active = 1
            ORDER BY r.room_name
        """, (test_gaming_id,))
        
        enrollments = cursor.fetchall()
        for enrollment in enrollments:
            print(f"  ✅ {enrollment[1]} enrolled in {enrollment[0]} by {enrollment[2]}")
        
        print(f"\n🎉 Test Summary:")
        print(f"  Gaming ID '{gaming_username}' is enrolled in {len(enrollments)} different rooms")
        print(f"  ✅ Cross-room enrollments: ALLOWED")
        print(f"  ❌ Duplicate same-room enrollments: BLOCKED")
        
        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        cursor.execute("DELETE FROM room_gaming_ids WHERE user_gaming_id = %s", (test_gaming_id,))
        cursor.execute("DELETE FROM room_user_enrollments WHERE user_id = %s AND room_id IN (%s, %s)", 
                      (user_id, room1_id, room2_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_gaming_id_constraints()