
import sqlite3
import os

# Define path matches db.py logic
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "desktop_assistant.db")

print(f"Checking database at: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("Database file not found!")
else:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "due_date" not in columns:
            print("Column 'due_date' missing. Adding it...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN due_date DATETIME")
            conn.commit()
            print("Migration successful: Added 'due_date' column.")
        else:
            print("Column 'due_date' already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")
