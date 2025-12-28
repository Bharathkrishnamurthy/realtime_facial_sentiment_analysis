import sqlite3, time, sys, json
db = "keystroke.db"
sid = sys.argv[1]    # pass session id as first arg
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
now = time.strftime("%Y-%m-%d %H:%M:%S")
# try common column names: status + started_at/started
try:
    cur.execute("UPDATE sessions SET status = ?, started_at = ? WHERE session_id = ?", ("active", now, sid))
    conn.commit()
except Exception:
    try:
        cur.execute("UPDATE sessions SET status = ?, started_at = ? WHERE session_id = ?", ("active", now, sid))
        conn.commit()
    except Exception as e:
        print("UPDATE error:", e)
# print the session row
r = cur.execute("SELECT * FROM sessions WHERE session_id = ?", (sid,)).fetchone()
if not r:
    print("NO SESSION ROW for", sid)
else:
    # print dict safely even if row is sqlite3.Row or tuple
    try:
        print(dict(r))
    except Exception:
        cols = [c[0] for c in cur.execute("PRAGMA table_info(sessions)").fetchall()]
        print({cols[i]: r[i] for i in range(len(cols))})
conn.close()
