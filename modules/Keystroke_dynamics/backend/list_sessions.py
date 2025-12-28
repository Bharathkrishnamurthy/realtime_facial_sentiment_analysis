import sqlite3
conn = sqlite3.connect("keystroke.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get real column names
cols = [c[1] for c in cur.execute("PRAGMA table_info(sessions)").fetchall()]
print("SESSION COLUMNS:", cols)

# Build safe SELECT using actual columns
sql = "SELECT * FROM sessions ORDER BY rowid DESC LIMIT 20"
rows = cur.execute(sql).fetchall()

if not rows:
    print("NO SESSIONS FOUND")
else:
    for r in rows:
        try:
            print(dict(r))
        except:
            print(tuple(r))

conn.close()
