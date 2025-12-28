import sqlite3, time
conn = sqlite3.connect('keystroke.db')
cur = conn.cursor()
# create a candidate (if not present)
cur.execute("INSERT OR IGNORE INTO candidates (id, name) VALUES (?, ?)", (1, "Demo Candidate"))
# create a test (if not present)
cur.execute("INSERT OR IGNORE INTO tests (id, name) VALUES (?, ?)", (1, "Demo Test"))
# create question (if not present)
cur.execute("INSERT OR IGNORE INTO questions (id, text) VALUES (?, ?)", (1, "Sample question text for enrollment"))
# link test->question. Try to detect whether test_questions has columns expected
try:
    cur.execute("INSERT OR IGNORE INTO test_questions (id, test_id, question_id, seq) VALUES (?, ?, ?, ?)", (1, 1, 1, 1))
except Exception:
    # fallback if seq isn't present
    try:
        cur.execute("INSERT OR IGNORE INTO test_questions (id, test_id, question_id) VALUES (?, ?, ?)", (1, 1, 1))
    except Exception:
        pass
# insert assignment/token
token = "fe5cf222-b59a-41ca-b30a-f7b7e32b3de2"
cur.execute("INSERT OR REPLACE INTO assignments (id, token, candidate_id, test_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (1, token, 1, 1, time.strftime('%Y-%m-%d %H:%M:%S')))
conn.commit()
print("Inserted demo assignment for token", token)
conn.close()
