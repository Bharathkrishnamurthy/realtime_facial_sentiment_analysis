# backend/app/create_tables.py
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "keystroke.db"   # adapt if your db is in a different location
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.executescript("""
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT UNIQUE,
  assignment_id INTEGER,
  candidate_id INTEGER,
  test_id INTEGER,
  started_at TEXT,
  finished_at TEXT,
  status TEXT
);

CREATE TABLE IF NOT EXISTS answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  question_id TEXT,
  final_text TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS keystroke_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  question_id TEXT,
  events_json TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS feature_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  question_id TEXT,
  mean_ht REAL,
  mean_dd REAL,
  cpm REAL,
  paste_flag INTEGER,
  created_at TEXT
);

-- minimal assignments table (for flow)
CREATE TABLE IF NOT EXISTS assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT UNIQUE,
  candidate_id INTEGER,
  test_id INTEGER,
  created_at TEXT
);

-- minimal questions/test relations if you don't have them
CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  text TEXT
);

CREATE TABLE IF NOT EXISTS test_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  test_id INTEGER,
  question_id INTEGER,
  seq INTEGER
);
""")
conn.commit()
conn.close()
print("DB created/updated at", db_path)
