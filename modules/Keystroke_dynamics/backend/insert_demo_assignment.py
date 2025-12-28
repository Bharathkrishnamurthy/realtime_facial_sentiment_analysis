# insert_demo_assignment.py
import sqlite3, time, traceback

DB = "keystroke.db"
token = "fe5cf222-b59a-41ca-b30a-f7b7e32b3de2"

conn = sqlite3.connect(DB)
cur = conn.cursor()

try:
    # add a sample question (id=1) if not present
    cur.execute("INSERT OR IGNORE INTO questions (id, text) VALUES (?, ?)", (1, "Sample question text for enrollment"))

    # add a mapping test_questions so test_id=1 has question_id=1
    cur.execute("INSERT OR IGNORE INTO test_questions (id, test_id, question_id, seq) VALUES (?, ?, ?, ?)",
                (1, 1, 1, 1))

    # insert an assignment token that candidate_routes expects
    # candidate_id and test_id are simple integers here (1). created_at is a string timestamp.
    cur.execute("INSERT OR IGNORE INTO assignments (token, candidate_id, test_id, created_at) VALUES (?, ?, ?, ?)",
                (token, 1, 1, time.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    print("Inserted demo rows (or they already existed). Token:", token)
except Exception as e:
    print("Error while inserting:", e)
    traceback.print_exc()
finally:
    conn.close()
