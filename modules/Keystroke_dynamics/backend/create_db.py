# check_db.py (put in backend folder)
import app.database as db

try:
    db.init_db()
except Exception as e:
    print("init_db() error:", e)

print("DB_PATH:", db.DB_PATH)

try:
    conn = db.get_conn()
    cur = conn.cursor()
    users = cur.execute("SELECT user_id, name, created_at FROM users ORDER BY created_at DESC LIMIT 50").fetchall()
    print("users:")
    for r in users:
        print(dict(r))
    conn.close()
except Exception as e:
    print("Error reading DB:", e)
