# backend/app/insert_demo_assignment.py
import sqlite3, uuid
from pathlib import Path

db_path = Path(__file__).parent / "keystroke.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Generate a token
token = str(uuid.uuid4())

# Create a sample question
c.execute("INSERT INTO questions (text) VALUES (?)", ("Sample question text for enrollment",))
qid = c.lastrowid

# Link question to test_id 1
c.execute("INSERT INTO test_questions (test_id, question_id, seq) VALUES (?,?,?)", (1, qid, 1))

# Insert assignment: token → test → candidate
c.execute("INSERT INTO assignments (token, candidate_id, test_id, created_at) VALUES (?,?,?,datetime('now'))",
          (token, 1, 1))

conn.commit()
print("New assignment token:", token)
conn.close()
