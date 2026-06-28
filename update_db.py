import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE attendance ADD COLUMN latitude TEXT")
except Exception as e:
    print(e)

try:
    cursor.execute("ALTER TABLE attendance ADD COLUMN longitude TEXT")
except Exception as e:
    print(e)

try:
    cursor.execute("ALTER TABLE attendance ADD COLUMN location_status TEXT")
except Exception as e:
    print(e)

conn.commit()
conn.close()

print("Done")