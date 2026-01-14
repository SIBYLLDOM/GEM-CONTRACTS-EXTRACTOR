import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "tender_automation_with_ai"
}

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    if conn.is_connected():
        print("Successfully connected to the database")
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()
        print(f"Connected to database: {db_name}")
        conn.close()
except Error as e:
    print(f"Error: {e}")
