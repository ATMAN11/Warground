import mysql.connector

def test_constraint_logic():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1111',
            database='gaming_platform'
        )
        cursor = conn.cursor()
        
        print('=== Checking Unique Constraint ===')
        cursor.execute("""
            SELECT CONSTRAINT_NAME, COLUMN_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = 'gaming_platform' 
            AND TABLE_NAME = 'room_gaming_ids' 
            AND CONSTRAINT_NAME = 'unique_gaming_id_per_room'
            ORDER BY ORDINAL_POSITION
        """)
        constraints = cursor.fetchall()
        
        if constraints:
            print("✅ Found unique constraint:")
            for constraint in constraints:
                print(f"  - {constraint[0]}: {constraint[1]}")
        else:
            print("❌ Unique constraint not found")
        
        print('\n=== Constraint Logic Explanation ===')
        print('Current constraint: UNIQUE(room_id, user_gaming_id)')
        print('')
        print('This means:')
        print('✅ ALLOWED: Same gaming ID in different rooms')
        print('   Example: Gaming ID "Player123" can join Room 1 AND Room 2')
        print('')
        print('❌ BLOCKED: Same gaming ID multiple times in same room') 
        print('   Example: Gaming ID "Player123" cannot join Room 1 twice')
        print('')
        
        # Test with sample data visualization
        print('=== Sample Scenarios ===')
        print('Scenario 1: ✅ VALID')
        print('  Room 1: Gaming ID "Player123"')
        print('  Room 2: Gaming ID "Player123"')
        print('  → Different rooms = ALLOWED')
        print('')
        print('Scenario 2: ❌ INVALID')
        print('  Room 1: Gaming ID "Player123" (first enrollment)')
        print('  Room 1: Gaming ID "Player123" (second enrollment)')
        print('  → Same room = BLOCKED by constraint')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    test_constraint_logic()