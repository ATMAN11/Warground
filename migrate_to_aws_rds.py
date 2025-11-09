#!/usr/bin/env python3
"""
AWS RDS Database Migration Script
This script helps migrate your database schema to AWS RDS
"""

import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection(host, user, password, database, port=3306):
    """Test database connection"""
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ Connection successful! MySQL version: {version[0]}")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def import_schema(host, user, password, database, schema_file, port=3306):
    """Import SQL schema file to RDS"""
    try:
        # Read schema file
        with open(schema_file, 'r', encoding='utf-8') as file:
            schema_content = file.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in schema_content.split(';') if stmt.strip()]
        
        # Connect to database
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset='utf8mb4'
        )
        
        print(f"📊 Importing {len(statements)} SQL statements...")
        
        with connection.cursor() as cursor:
            success_count = 0
            for i, statement in enumerate(statements, 1):
                try:
                    cursor.execute(statement)
                    success_count += 1
                    print(f"✅ Statement {i}/{len(statements)} executed successfully")
                except Exception as e:
                    print(f"⚠️  Statement {i} failed: {e}")
                    print(f"Statement: {statement[:100]}...")
        
        connection.commit()
        connection.close()
        
        print(f"🎉 Schema import completed! {success_count}/{len(statements)} statements successful")
        return True
        
    except Exception as e:
        print(f"❌ Schema import failed: {e}")
        return False

def verify_tables(host, user, password, database, port=3306):
    """Verify that tables were created successfully"""
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print(f"📋 Found {len(tables)} tables in database:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"   - {table[0]}: {count} records")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Table verification failed: {e}")
        return False

def main():
    """Main migration process"""
    print("🚀 AWS RDS Migration Tool for Gaming Platform")
    print("=" * 50)
    
    # Get RDS connection details
    print("\n📝 Enter your AWS RDS connection details:")
    host = input("RDS Endpoint (e.g., gaming-platform-db.xxxxxxxxx.region.rds.amazonaws.com): ").strip()
    user = input("Master Username (default: admin): ").strip() or "admin"
    password = input("Master Password: ").strip()
    database = input("Database Name (default: gaming_platform): ").strip() or "gaming_platform"
    port = int(input("Port (default: 3306): ").strip() or "3306")
    
    print(f"\n🔌 Testing connection to {host}...")
    
    # Test connection
    if not test_connection(host, user, password, database, port):
        print("❌ Cannot proceed without valid database connection")
        return
    
    # Import schema
    schema_file = "complete_database_schema.sql"
    if not os.path.exists(schema_file):
        print(f"❌ Schema file '{schema_file}' not found!")
        print("Make sure you're running this script from the project directory")
        return
    
    print(f"\n📥 Importing schema from {schema_file}...")
    if not import_schema(host, user, password, database, schema_file, port):
        print("❌ Schema import failed")
        return
    
    # Verify tables
    print(f"\n🔍 Verifying table creation...")
    verify_tables(host, user, password, database, port)
    
    # Generate Railway environment variables
    print(f"\n📋 Railway Environment Variables:")
    print("=" * 40)
    print(f"MYSQL_HOST={host}")
    print(f"MYSQL_USER={user}")
    print(f"MYSQL_PASSWORD={password}")
    print(f"MYSQL_DB={database}")
    print(f"MYSQL_PORT={port}")
    print("FLASK_ENV=production")
    print("SECRET_KEY=change-this-to-something-secure")
    print("PORT=8080")
    
    print(f"\n✅ Migration completed successfully!")
    print(f"🎯 Next steps:")
    print(f"   1. Copy the environment variables above to Railway")
    print(f"   2. Redeploy your Railway application")
    print(f"   3. Test your app at your-app.railway.app/health")

if __name__ == "__main__":
    main()