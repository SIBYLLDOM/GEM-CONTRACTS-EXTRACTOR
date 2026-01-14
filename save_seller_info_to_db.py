"""
Phase 3C: Save Extracted Seller Information to Database
Updates the 'contracts' table with seller details from seller_info.csv
Matches records using 'bid_no' as the identifier
"""

import csv
import mysql.connector
from mysql.connector import Error
from pathlib import Path

# Database Configuration (matching controller/contracts_controller.py)
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "tender_automation_with_ai"
}

CSV_FILE = "data/seller_info.csv"

def connect_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("[DB] ✅ Connected to database")
        return conn
    except Error as e:
        print(f"[DB] ❌ Connection error: {e}")
        return None

def prepare_table(conn):
    """Add missing columns to the contracts table if they don't exist."""
    cursor = conn.cursor()
    
    # Columns to add
    new_columns = [
        ("seller_id", "VARCHAR(100)"),
        ("seller_name", "TEXT"),
        ("seller_email", "VARCHAR(255)"),
        ("unit_price", "VARCHAR(50)")
    ]
    
    # Check existing columns
    cursor.execute("DESCRIBE contracts")
    existing_columns = [col[0] for col in cursor.fetchall()]
    
    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            print(f"[DB] ➕ Adding column: {col_name}")
            cursor.execute(f"ALTER TABLE contracts ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    cursor.close()

def update_db_from_csv(conn):
    """Read CSV and update database records."""
    if not Path(CSV_FILE).exists():
        print(f"[CSV] ❌ File not found: {CSV_FILE}")
        return

    cursor = conn.cursor()
    
    success_count = 0
    total_count = 0
    
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_count += 1
            bid_no = row.get('bid_no')
            
            if not bid_no:
                continue
                
            # Update query
            # We match on bid_no
            query = """
            UPDATE contracts 
            SET seller_id = %s, 
                seller_name = %s, 
                seller_email = %s, 
                unit_price = %s
            WHERE bid_no = %s
            """
            params = (
                row.get('seller_id'),
                row.get('seller_name'),
                row.get('seller_email'),
                row.get('unit_price'),
                bid_no
            )
            
            try:
                cursor.execute(query, params)
                if cursor.rowcount > 0:
                    success_count += 1
            except Error as e:
                print(f"[DB] ❌ Error updating bid {bid_no}: {e}")

    conn.commit()
    cursor.close()
    
    print("\n" + "=" * 50)
    print(f"📊 DATABASE UPDATE SUMMARY")
    print("=" * 50)
    print(f"✅ Records matched and updated: {success_count}")
    print(f"📝 Total records in CSV: {total_count}")
    print(f"❌ Records not found in DB: {total_count - success_count}")
    print("=" * 50)

if __name__ == "__main__":
    print("🚀 Starting Database Update (Phase 3C)...")
    
    connection = connect_db()
    if connection:
        try:
            prepare_table(connection)
            update_db_from_csv(connection)
        finally:
            connection.close()
            print("[DB] 🔒 Connection closed")
