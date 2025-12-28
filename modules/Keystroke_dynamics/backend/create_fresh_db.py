import sqlite3, os
db = "app/keystroke.db"
if os.path.exists(db):
    os.remove(db)
conn = sqlite3.connect(db)
cur = conn.cursor()
# minimal schema (examples) - adapt later if your app expects more columns
cur.executescript("""
CREATE TABLE IF NOT EXISTS assignments(id INTEGER PRIMARY KEY AUTOINCREMENT, token TEXT UNIQUE, candidate_id INTEGER, test_id INTEGER, created_at TEXT);
CREATE TABLE IF NOT EXISTS tests(id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY, text TEXT);
CREATE TABLE IF NOT EXISTS test_questions(id INTEGER PRIMARY KEY AUTOINCREMENT, test_id INTEGER, question_id INTEGER, seq INTEGER);
CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT UNIQUE, assignment_id INTEGER, candidate_id INTEGER, test_id INTEGER, started_at TEXT, finished_at TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS answers(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, question_id TEXT, final_text TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS feature_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, question_id TEXT, meta TEXT, created_at TEXT);
""")
conn.commit()
conn.close()
print("Created fresh DB at", db)
