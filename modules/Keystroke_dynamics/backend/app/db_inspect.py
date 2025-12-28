# db_inspect.py
# Usage: python app/db_inspect.py
import sqlite3
import numpy as np
import sys
from datetime import datetime

DB = "keystroke.db"

def print_tables(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    rows = cur.fetchall()
    print("Tables:")
    for r in rows:
        print(" -", r[0])

def profiles_summary(conn):
    cur = conn.cursor()
    cur.execute("SELECT user_id, COUNT(*), MIN(created_at), MAX(created_at) FROM profiles GROUP BY user_id;")
    rows = cur.fetchall()
    print("\\nProfiles summary (user_id, count, min_created, max_created):")
    if not rows:
        print(" (no profiles found)")
    for r in rows:
        min_ts = datetime.fromtimestamp(r[2]).isoformat() if r[2] else "NULL"
        max_ts = datetime.fromtimestamp(r[3]).isoformat() if r[3] else "NULL"
        print(f" - {r[0]}  count={r[1]}  created_range={min_ts} .. {max_ts}")

def recent_sessions(conn, limit=10):
    cur = conn.cursor()
    cur.execute("SELECT session_id, user_id, question_id, score, verdict, paste_flag, timestamp FROM sessions ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    print(f"\\nLast {limit} sessions:")
    if not rows:
        print(" (no sessions found)")
    for r in rows:
        ts = datetime.fromtimestamp(r[6]).isoformat() if r[6] else "NULL"
        print(f" - session={r[0]} user={r[1]} q={r[2]} score={r[3]} verdict={r[4]} paste={r[5]} ts={ts}")

def dump_one_profile(conn, user_id):
    cur = conn.cursor()
    cur.execute("SELECT id, embedding, created_at FROM profiles WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    print(f"\\nProfiles for user {user_id}: {len(rows)}")
    for idx, r in enumerate(rows):
        eid, emb_blob, created_at = r
        created = datetime.fromtimestamp(created_at).isoformat() if created_at else "NULL"
        if emb_blob:
            try:
                vec = np.frombuffer(emb_blob, dtype=np.float32)
                print(f"  - id={eid} created={created} vec_len={vec.size} first8={vec[:8].tolist()}")
            except Exception as e:
                print(f"  - id={eid} created={created} (could not parse embedding: {e})")
        else:
            print(f"  - id={eid} created={created} (no blob)")

def main():
    try:
        conn = sqlite3.connect(DB)
    except Exception as e:
        print("Could not open DB:", e)
        sys.exit(1)
    print_tables(conn)
    profiles_summary(conn)
    recent_sessions(conn, limit=20)
    # If a user id is provided as arg, dump that user's profiles
    if len(sys.argv) >= 2:
        user_id = sys.argv[1]
        dump_one_profile(conn, user_id)
    conn.close()

if __name__ == '__main__':
    main()
