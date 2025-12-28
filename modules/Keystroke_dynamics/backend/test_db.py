# test_db.py — prints table names and up to 5 rows per table (readable)
import app.database as db
import sqlite3, json

conn = db.get_db()
conn.row_factory = sqlite3.Row
cur = conn.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Connected DB tables:", tables)
print("-----\n")

for t in tables:
    try:
        rows = cur.execute(f"SELECT * FROM {t} LIMIT 5").fetchall()
    except Exception as e:
        print(f"Cannot read table {t}: {e}")
        continue
    print(f"Table: {t}  (showing up to 5 rows)")
    if not rows:
        print("  (no rows)\n")
        continue
    for r in rows:
        # convert sqlite3.Row to dict for pretty printing
        d = dict(r)
        print("  ", json.dumps(d, default=str))
    print("-----\n")

conn.close()
