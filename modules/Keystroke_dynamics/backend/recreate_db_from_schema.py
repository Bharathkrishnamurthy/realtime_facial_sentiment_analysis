# recreate_db_from_schema.py
# Usage: python recreate_db_from_schema.py
import sqlite3, time, shutil, os, sys, json
from datetime import datetime

DB_PATH = "app/keystroke.db"

def backup_db(path):
    if os.path.exists(path):
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        bak = path + ".corrupt_backup_" + ts
        shutil.copy2(path, bak)
        print("Backed up existing DB to:", bak)
    else:
        print("No existing DB found at", path)

SCHEMA_SQL = r"""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE,
    name TEXT,
    email TEXT,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,               -- link to users.user_id
    name TEXT,
    email TEXT,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    time_limit_minutes INTEGER,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    qtype TEXT DEFAULT 'theory',
    options_json TEXT,
    correct_answer TEXT,
    topic TEXT,
    difficulty TEXT,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS test_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    seq INTEGER DEFAULT 0,
    FOREIGN KEY(test_id) REFERENCES tests(id),
    FOREIGN KEY(question_id) REFERENCES questions(id)
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE,
    candidate_id INTEGER,
    test_id INTEGER,
    created_at TEXT,
    FOREIGN KEY(candidate_id) REFERENCES candidates(id),
    FOREIGN KEY(test_id) REFERENCES tests(id)
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE,
    assignment_id INTEGER,
    candidate_id INTEGER,
    test_id INTEGER,
    started_at TEXT,
    finished_at TEXT,
    status TEXT,
    FOREIGN KEY(assignment_id) REFERENCES assignments(id),
    FOREIGN KEY(candidate_id) REFERENCES candidates(id),
    FOREIGN KEY(test_id) REFERENCES tests(id)
);

CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    question_id TEXT,
    final_text TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS feature_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    question_id TEXT,
    meta TEXT,
    created_at TEXT
);

-- Small index hints
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_assignments_token ON assignments(token);
CREATE INDEX IF NOT EXISTS idx_questions_id ON questions(id);
"""

DEMO_INSERTS = [
    # demo candidate
    ("INSERT OR IGNORE INTO candidates (id, user_id, name, email, created_at) VALUES (?, ?, ?, ?, ?)",
     (1, "demo_user_1", "Demo Candidate", "demo@example.com", int(time.time()))),

    # demo test
    ("INSERT OR IGNORE INTO tests (id, name, description, time_limit_minutes, created_at) VALUES (?, ?, ?, ?, ?)",
     (1, "Demo Coverage Test", "Coverage + interview demo test", 30, int(time.time()))),

    # seed coverage questions (ids 1001..1006)
    ("INSERT OR IGNORE INTO questions (id, text, qtype, created_at) VALUES (?, ?, ?, ?)",
     (1001, "Please write: my keyboard test contains commas, periods. does it work? yes!", "theory", int(time.time()))),

    ("INSERT OR IGNORE INTO questions (id, text, qtype, created_at) VALUES (?, ?, ?, ?)",
     (1002, "Type: AbCdEFg 12345", "theory", int(time.time()))),

    ("INSERT OR IGNORE INTO questions (id, text, qtype, created_at) VALUES (?, ?, ?, ?)",
     (1003, "The quick brown fox jumps over the lazy dog.", "theory", int(time.time()))),

    ("INSERT OR IGNORE INTO questions (id, text, qtype, created_at) VALUES (?, ?, ?, ?)",
     (1004, "Symbols: ! @ # $ % ^ & * ( ) - _ = + [ ] { } ; : ' \" , . < > / ? \\ | ` ~", "theory", int(time.time()))),

    ("INSERT OR IGNORE INTO questions (id, text, qtype, created_at) VALUES (?, ?, ?, ?)",
     (1005, "Numbers: 0123456789. Try math 25+5=30; 3.14 approx.", "theory", int(time.time()))),

    ("INSERT OR IGNORE INTO questions (id, text, qtype, created_at) VALUES (?, ?, ?, ?)",
     (1006, "Please type a two-line response (press Enter once) to demonstrate Enter key usage.", "theory", int(time.time()))),

    # link to test_questions
    ("INSERT OR IGNORE INTO test_questions (test_id, question_id, seq) VALUES (?, ?, ?)", (1, 1001, 1)),
    ("INSERT OR IGNORE INTO test_questions (test_id, question_id, seq) VALUES (?, ?, ?)", (1, 1002, 2)),
    ("INSERT OR IGNORE INTO test_questions (test_id, question_id, seq) VALUES (?, ?, ?)", (1, 1003, 3)),
    ("INSERT OR IGNORE INTO test_questions (test_id, question_id, seq) VALUES (?, ?, ?)", (1, 1004, 4)),
    ("INSERT OR IGNORE INTO test_questions (test_id, question_id, seq) VALUES (?, ?, ?)", (1, 1005, 5)),
    ("INSERT OR IGNORE INTO test_questions (test_id, question_id, seq) VALUES (?, ?, ?)", (1, 1006, 6)),

    # assignment token for quick demo (your token)
    ("INSERT OR IGNORE INTO assignments (id, token, candidate_id, test_id, created_at) VALUES (?, ?, ?, ?, ?)",
     (1, "fe5cf222-b59a-41ca-b30a-f7b7e32b3de2", 1, 1, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))),
]

def recreate():
    backup_db(DB_PATH)

    # ensure folder exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    print("Creating schema...")
    cur.executescript(SCHEMA_SQL)
    conn.commit()
    print("Schema created.")

    print("Inserting demo rows...")
    for sql, params in DEMO_INSERTS:
        try:
            cur.execute(sql, params)
        except Exception as e:
            print("Warning inserting demo:", e)
    conn.commit()

    # quick sanity checks
    res = cur.execute("PRAGMA integrity_check").fetchall()
    print("PRAGMA integrity_check ->", res)
    conn.close()
    print("Done. New DB created at:", DB_PATH)

if __name__ == "__main__":
    try:
        recreate()
    except Exception as e:
        print("Failed:", e)
        sys.exit(1)
