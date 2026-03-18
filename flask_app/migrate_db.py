"""
Database migration script to add new columns
Run this once to update your existing database
"""
import sqlite3
import os
from datetime import datetime

db_path = os.path.join(os.path.dirname(__file__), 'app.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    new_columns = [
        ('negative_streak', 'INTEGER DEFAULT 0'),
        ('is_learned', 'BOOLEAN DEFAULT 0'),
        ('times_reviewed', 'INTEGER DEFAULT 0'),
        ('times_shown', 'INTEGER DEFAULT 0'),
        ('next_review', 'TIMESTAMP'),
    ]
    
    try:
        cursor.execute("PRAGMA table_info(user_word_stats)")
        columns = [col[1] for col in cursor.fetchall()]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                print(f"Adding {col_name} column...")
                cursor.execute(f"ALTER TABLE user_word_stats ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"[OK] Successfully added {col_name} column")
            else:
                print(f"[OK] {col_name} column already exists")
                
        print("\n[OK] Migration complete!")
                
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
else:
    print("No database found. It will be created when you start the app.")
