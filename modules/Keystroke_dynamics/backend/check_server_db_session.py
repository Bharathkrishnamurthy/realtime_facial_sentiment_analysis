import app.database as database, sqlite3, sys
# print the file used by the server-side DB helper (so we check the same file)
conn = database.get_db()
print("PRAGMA database_list ->", conn.execute("PRAGMA database_list").fetchall())
conn.row_factory = sqlite3.Row
# paste the session id you got from /candidate/start below:
sid = "'" + sys.argv[1] + "'"
r = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (sys.argv[1],)).fetchone()
print("SESSION ROW:", dict(r) if r else "NO SESSION")
conn.close()
