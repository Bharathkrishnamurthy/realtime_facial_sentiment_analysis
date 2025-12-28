# backend/check_users.py
import app.database as db

print("DB_PATH:", db.DB_PATH)
try:
    conn = db.get_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT user_id, created_at FROM users ORDER BY created_at DESC").fetchall()
    print("users:")
    for r in rows:
        # handle sqlite3.Row or plain tuples
        try:
            print(dict(r))
        except Exception:
            print(tuple(r))
    conn.close()
except Exception as e:
    print("Error when reading users:", repr(e))
    