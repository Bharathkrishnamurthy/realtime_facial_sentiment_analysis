import sqlite3, time, sys
dbpath = "app/keystroke.db"   # <- replace this with the file the server PRAGMA showed if different
sid = sys.argv[1]
conn = sqlite3.connect(dbpath)
cur = conn.cursor()
now = time.strftime('%Y-%m-%d %H:%M:%S')
cur.execute("UPDATE sessions SET status = ?, started_at = ? WHERE session_id = ?", ('active', now, sid))
conn.commit()
r = conn.execute('SELECT * FROM sessions WHERE session_id = ?', (sid,)).fetchone()
print("Session after update:", dict(r) if r else "NO SESSION")
conn.close()
