# show_sessions_schema.py
import sqlite3, json
conn = sqlite3.connect("keystroke.db")
cur = conn.cursor()
rows = cur.execute("PRAGMA table_info('sessions')").fetchall()
print("sessions schema (PRAGMA table_info):")
for r in rows:
    print(r)
conn.close()
