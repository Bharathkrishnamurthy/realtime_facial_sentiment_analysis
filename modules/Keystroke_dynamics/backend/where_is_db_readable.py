import app.database as database
conn = database.get_db()
# PRAGMA database_list returns rows with columns: seq, name, file
rows = conn.execute("PRAGMA database_list").fetchall()
# try to print full info in a readable way
for r in rows:
    try:
        # r may be sqlite3.Row
        print("PRAGMA DB row ->", dict(r))
    except Exception:
        print("PRAGMA DB row raw ->", r)
conn.close()
