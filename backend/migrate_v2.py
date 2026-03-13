
import sqlite3
import os

# Define path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "desktop_assistant.db")
print(f"Migrating V2 Database at: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("No database found to migrate. It will be created fresh by the app.")
    exit()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def add_column_if_not_exists(table, column, type_def):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
        print(f"Added {column} to {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            pass # Already exists
        else:
            print(f"Skipping {column} in {table} (already exists or error: {e})")

# Migrate Tasks
add_column_if_not_exists("tasks", "description", "TEXT")
add_column_if_not_exists("tasks", "priority", "TEXT DEFAULT 'medium'")
add_column_if_not_exists("tasks", "status", "TEXT DEFAULT 'pending'")
add_column_if_not_exists("tasks", "reminder_time", "DATETIME")
add_column_if_not_exists("tasks", "tags", "TEXT")
add_column_if_not_exists("tasks", "updated_at", "DATETIME")

# Migrate Notes
add_column_if_not_exists("notes", "title", "TEXT")
add_column_if_not_exists("notes", "linked_task_id", "INTEGER")
add_column_if_not_exists("notes", "updated_at", "DATETIME")

# Create Plans Table (if not exists)
cursor.execute("""
CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    target_date DATETIME,
    progress INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
print("Ensured 'plans' table exists.")

conn.commit()
conn.close()
print("Migration V2 Complete.")
