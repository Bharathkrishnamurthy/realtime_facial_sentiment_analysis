# seed_demo.py (SAFE VERSION for your current schema)
# Run: python seed_demo.py

import sqlite3, uuid, os, time
from datetime import datetime

DB = os.path.join("app", "keystroke.db")

def now_str():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("Connected to DB:", DB)

# ------------------------
# 1) Insert a Question
# ------------------------
question_text = "Type this exact sentence: The quick brown fox jumps over the lazy dog."
cur.execute(
    "INSERT INTO questions (text, description) VALUES (?, ?)",
    (question_text, "demo typing")
)
q_id = cur.lastrowid
print("Created question_id:", q_id)

# ------------------------
# 2) Insert Test (NO time_limit column since your DB doesn't have it)
# ------------------------
cur.execute(
    "INSERT INTO tests (name, description) VALUES (?, ?)",
    ("Demo Test", "Demo test for keystroke flow")
)
test_id = cur.lastrowid
print("Created test_id:", test_id)

# Link question to test
try:
    cur.execute(
        "INSERT INTO test_questions (test_id, question_id, seq) VALUES (?, ?, ?)",
        (test_id, q_id, 1)
    )
except Exception:
    # fallback for old schema without seq
    cur.execute(
        "INSERT INTO test_questions (test_id, question_id) VALUES (?, ?)",
        (test_id, q_id)
    )
print("Linked question to test")

# ------------------------
# 3) Create demo user + candidate
# ------------------------
user_id = str(uuid.uuid4())
cur.execute(
    "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
    (user_id, int(time.time()))
)

cur.execute(
    "INSERT INTO candidates (name, email) VALUES (?, ?)",
    ("Demo Candidate", "demo@example.com")
)
candidate_id = cur.lastrowid
print("Created candidate_id:", candidate_id)

# ------------------------
# 4) Create assignment with TOKEN
# ------------------------
token = str(uuid.uuid4())
created_at = now_str()

# your schema: token, candidate_id, test_id, created_at
cur.execute(
    "INSERT INTO assignments (token, candidate_id, test_id, created_at) VALUES (?, ?, ?, ?)",
    (token, candidate_id, test_id, created_at)
)
assignment_id = cur.lastrowid

conn.commit()
conn.close()

print("\n--- SEED COMPLETE ---")
print("question_id:", q_id)
print("test_id:", test_id)
print("candidate_id:", candidate_id)
print("assignment_id:", assignment_id)
print("\nUSE THIS TOKEN:\n", token)
print("\nStart test with:\nPOST /candidate/start  { \"token\": \"" + token + "\" }")
