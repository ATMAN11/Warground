#!/usr/bin/env python3
"""
Database Schema Analysis Script
Checks the current database structure and compares with application requirements
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', '1111'),
            database=os.getenv('MYSQL_DB', 'gaming_platform')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def analyze_database_schema():
    """Analyze current database schema"""
    connection = get_db_connection()
    if not connection:
        print("❌ Could not connect to database")
        return
    
    cursor = connection.cursor()
    
    try:
        print("🔍 ANALYZING DATABASE SCHEMA")
        print("=" * 50)
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No tables found in database!")
            return
        
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"  ✅ {table[0]}")
        
        print("\n" + "=" * 50)
        
        # Analyze each table structure
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            print("-" * 30)
            
            # Get table structure
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                field, type_info, null, key, default, extra = col
                key_info = f" ({key})" if key else ""
                null_info = "NULL" if null == "YES" else "NOT NULL"
                default_info = f" DEFAULT {default}" if default else ""
                extra_info = f" {extra}" if extra else ""
                print(f"  - {field}: {type_info}{key_info} {null_info}{default_info}{extra_info}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  📊 Rows: {count}")
        
        print("\n" + "=" * 50)
        print("🔍 CHECKING FOR REQUIRED TABLES")
        print("=" * 50)
        
        # Required tables for the application
        required_tables = [
            'users',
            'rooms', 
            'user_gaming_ids',
            'user_gaming_id_stats',
            'room_user_enrollments',
            'room_gaming_ids',
            'gaming_id_room_stats',
            'room_team_enrollments',
            'user_teams',
            'transactions',
            'withdrawals',
            'room_winners',
            'room_reward_settings',
            'winner_selection_history',
            'blocked_users',
            'blocked_teams'
        ]
        
        existing_tables = [table[0] for table in tables]
        
        missing_tables = []
        for required in required_tables:
            if required in existing_tables:
                print(f"  ✅ {required}")
            else:
                print(f"  ❌ {required} - MISSING")
                missing_tables.append(required)
        
        if missing_tables:
            print(f"\n⚠️  MISSING TABLES: {len(missing_tables)}")
            for table in missing_tables:
                print(f"  - {table}")
            print("\nYou need to run the complete database.sql file to create missing tables.")
        else:
            print("\n✅ All required tables are present!")
        
        print("\n" + "=" * 50)
        print("🔍 CHECKING CRITICAL RELATIONSHIPS")
        print("=" * 50)
        
        # Check foreign key relationships
        if 'user_gaming_ids' in existing_tables and 'users' in existing_tables:
            cursor.execute("""
                SELECT COUNT(*) FROM user_gaming_ids ugi 
                LEFT JOIN users u ON ugi.user_id = u.id 
                WHERE u.id IS NULL
            """)
            orphaned_gaming_ids = cursor.fetchone()[0]
            if orphaned_gaming_ids > 0:
                print(f"  ⚠️  {orphaned_gaming_ids} orphaned gaming IDs (no matching user)")
            else:
                print("  ✅ All gaming IDs have valid users")
        
        if 'room_user_enrollments' in existing_tables and 'rooms' in existing_tables:
            cursor.execute("""
                SELECT COUNT(*) FROM room_user_enrollments rue 
                LEFT JOIN rooms r ON rue.room_id = r.id 
                WHERE r.id IS NULL
            """)
            orphaned_enrollments = cursor.fetchone()[0]
            if orphaned_enrollments > 0:
                print(f"  ⚠️  {orphaned_enrollments} orphaned room enrollments")
            else:
                print("  ✅ All room enrollments have valid rooms")
        
        print("\n" + "=" * 50)
        print("📊 DATA SUMMARY")
        print("=" * 50)
        
        # Show data counts for important tables
        summary_tables = ['users', 'rooms', 'user_gaming_ids', 'room_user_enrollments']
        for table_name in summary_tables:
            if table_name in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  {table_name}: {count} records")
        
    except Error as e:
        print(f"❌ Error analyzing database: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print(f"\n🔌 Database connection closed")

if __name__ == "__main__":
    analyze_database_schema()