import sqlite3
import os
import json

# DB is in the same folder as this script
DB_PATH = os.path.join(os.path.dirname(__file__), "keystroke.db")

print("Using DB:", DB_PATH)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1) List tables
print("\nTables in DB:")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
for (name,) in cur.fetchall():
    print(" -", name)

# 2) How many samples total
print("\nSample counts:")
for table in ("keystroke_samples", "sessions", "users", "keystroke_templates"):
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        (cnt,) = cur.fetchone()
        print(f" {table}: {cnt}")
    except Exception as e:
        print(f" {table}: <no such table> ({e})")

# 3) Show last 5 keystroke_samples rows (id, user, verdict, created_at)
print("\nLast 5 samples:")
try:
    cur.execute("""
        SELECT id, user_id, verdict, score, paste_flag, created_at
        FROM keystroke_samples
        ORDER BY id DESC
        LIMIT 5
    """)
    rows = cur.fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print("Error reading keystroke_samples:", e)

# 4) Optionally print meta JSON for the latest sample (to see features)
print("\nLatest sample meta_json (truncated):")
try:
    cur.execute("""
        SELECT meta_json
        FROM keystroke_samples
        ORDER BY id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        meta = json.loads(row[0])
        # just show a few keys
        keys_to_show = ["median_ht","median_dd","cpm","pauses_over_200",
                        "blur_count","paste_detected_explicit","paste_detected_heuristic"]
        for k in keys_to_show:
            print(f" {k}: {meta.get(k)}")
    else:
        print(" No samples yet.")
except Exception as e:
    print("Error reading latest meta_json:", e)

conn.close()
