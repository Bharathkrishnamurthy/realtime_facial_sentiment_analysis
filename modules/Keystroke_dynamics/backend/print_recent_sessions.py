import app.database as database
import sqlite3, sys

conn = database.get_db()
conn.row_factory = sqlite3.Row
cur = conn.cursor()
# To print all recent sessions:
rows = cur.execute("SELECT * FROM sessions ORDER BY rowid DESC LIMIT 20").fetchall()
print("Recent sessions (server DB):")
for r in rows:
    print(dict(r))
conn.close()
