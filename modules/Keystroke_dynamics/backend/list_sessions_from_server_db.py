import app.database as database
conn = database.get_db()
conn.row_factory = __import__('sqlite3').Row
rows = conn.execute("SELECT * FROM sessions ORDER BY rowid DESC LIMIT 20").fetchall()
if not rows:
    print("NO rows in sessions (server DB).")
else:
    for r in rows:
        try:
            print(dict(r))
        except Exception:
            print(r)
conn.close()
