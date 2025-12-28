# set_session_active.py
import app.database as database
from datetime import datetime
import sys

# session id passed as first arg, else uses built-in example
sid = sys.argv[1] if len(sys.argv) > 1 else "17e871a9-91f0-4ba9-a73b-aab1e4b14683"

conn = database.get_db()
conn.row_factory = __import__('sqlite3').Row
cur = conn.cursor()

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
# Try updating started_at and status (robust to missing columns)
try:
    cur.execute("UPDATE sessions SET status = ?, started_at = ? WHERE session_id = ?", ("active", now, sid))
    conn.commit()
except Exception as e:
    # fallback if started_at doesn't exist, only set status (or if status doesn't exist this will fail)
    try:
        cur.execute("UPDATE sessions SET status = ? WHERE session_id = ?", ("active", sid))
        conn.commit()
    except Exception as e2:
        print("ERROR updating session:", e, e2)
        conn.close()
        raise

# print the session row back for verification
r = cur.execute("SELECT * FROM sessions WHERE session_id = ?", (sid,)).fetchone()
print("Session after update:" , dict(r) if r else "NO SESSION")
conn.close()
