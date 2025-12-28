import app.database as database
import sqlite3

conn = database.get_db()
cur = conn.cursor()
cols = [c[1] for c in cur.execute("PRAGMA table_info(sessions)").fetchall()]
print("Existing sessions columns:", cols)
if "status" not in cols:
    print("Adding 'status' column to sessions table...")
    cur.execute("ALTER TABLE sessions ADD COLUMN status TEXT DEFAULT 'pending'")
    conn.commit()
    print("'status' column added.")
else:
    print("'status' column already present, no change.")
conn.close()
