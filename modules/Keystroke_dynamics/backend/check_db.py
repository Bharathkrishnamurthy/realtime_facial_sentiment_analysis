import sqlite3
import json

DB_PATH = "keystroke.db"   # already correct, you can see tables so don't change

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("\n=== Tables Available ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cur.fetchall())

print("\n=== keystroke_samples count ===")
cur.execute("SELECT COUNT(*) FROM keystroke_samples;")
count = cur.fetchone()[0]
print(count)

print("\n=== Last 3 Stored Samples ===")
if count == 0:
    print("No rows yet in keystroke_samples.")
else:
    cur.execute("""
        SELECT id, user_id, question_id, score, verdict, meta_json
        FROM keystroke_samples
        ORDER BY id DESC
        LIMIT 3;
    """)
    rows = cur.fetchall()

    for r in rows:
        row_id, user_id, question_id, score, verdict, meta_json = r
        print("\nRow ID:", row_id)
        print("User:", user_id)
        print("Question:", question_id)
        print("Score:", score)
        print("Verdict:", verdict)

        meta = {}
        if meta_json:
            try:
                meta = json.loads(meta_json)
            except Exception:
                pass

        print("frontend_rhythm_sim:", meta.get("frontend_rhythm_sim"))
        print("frontend_text_sim:", meta.get("frontend_text_sim"))
        print("frontend_param_sims:", meta.get("frontend_param_sims"))
        print("paste_flag (from meta if present):", meta.get("paste_flag"))

conn.close()
