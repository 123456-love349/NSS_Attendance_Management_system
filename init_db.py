import sqlite3
import os

def init_db():
    db_path = 'database.db'
    schema_path = 'schema.sql'
    
    print(f"Initializing database at: {os.path.abspath(db_path)}")
    
    # Connect and execute schema
    conn = sqlite3.connect(db_path)
    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
