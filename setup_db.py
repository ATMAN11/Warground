#!/usr/bin/env python3
"""
Database setup script for production deployment
"""

import os
import mysql.connector
from mysql.connector import Error

def setup_database():
    """Setup database tables and initial data"""
    
    # Database connection parameters
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DB', 'gaming_platform')
    }
    
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print("Connected to MySQL database")
        
        # Read and execute SQL file
        with open('database.sql', 'r') as sql_file:
            sql_script = sql_file.read()
        
        # Split and execute each statement
        statements = sql_script.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                    print(f"Executed: {statement[:50]}...")
                except Error as e:
                    if "already exists" not in str(e):
                        print(f"Error executing statement: {e}")
        
        connection.commit()
        print("Database setup completed successfully!")
        
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")

if __name__ == "__main__":
    setup_database()