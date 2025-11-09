#!/usr/bin/env python3

import mysql.connector

# Database configuration
config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1111',
    'database': 'gaming_platform'
}

def fix_team_sizes():
    """Update team_size field for all existing teams based on actual member count"""
    
    try:
        # Connect to database
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        print("Fixing team sizes for existing teams...")
        
        # Get all teams
        cursor.execute("SELECT id, team_name FROM user_teams")
        teams = cursor.fetchall()
        
        updated_count = 0
        
        for team_id, team_name in teams:
            # Count actual members for this team
            cursor.execute("""
                SELECT COUNT(*) FROM user_team_members 
                WHERE user_team_id = %s
            """, (team_id,))
            
            actual_member_count = cursor.fetchone()[0]
            
            # Update team_size
            cursor.execute("""
                UPDATE user_teams 
                SET team_size = %s 
                WHERE id = %s
            """, (actual_member_count, team_id))
            
            print(f"Team '{team_name}' (ID: {team_id}): Updated team_size to {actual_member_count}")
            updated_count += 1
        
        # Commit changes
        conn.commit()
        print(f"\n✅ Successfully updated {updated_count} teams!")
        
        # Verify the fix
        print("\n=== VERIFICATION ===")
        cursor.execute("""
            SELECT ut.id, ut.team_name, ut.team_size, COUNT(utm.id) as actual_members
            FROM user_teams ut
            LEFT JOIN user_team_members utm ON ut.id = utm.user_team_id
            GROUP BY ut.id
            ORDER BY ut.id
        """)
        
        verification_results = cursor.fetchall()
        all_correct = True
        
        for team_id, team_name, stored_size, actual_size in verification_results:
            status = "✅" if stored_size == actual_size else "❌"
            print(f"{status} Team '{team_name}': stored={stored_size}, actual={actual_size}")
            if stored_size != actual_size:
                all_correct = False
        
        if all_correct:
            print("\n🎉 All team sizes are now correctly synchronized!")
        else:
            print("\n⚠️ Some inconsistencies remain. Please check manually.")
            
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_team_sizes()