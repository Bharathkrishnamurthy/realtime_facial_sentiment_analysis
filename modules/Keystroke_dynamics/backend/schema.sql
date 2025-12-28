PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  created_at INTEGER
);

CREATE TABLE IF NOT EXISTS profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  template_version INTEGER DEFAULT 1,
  embedding BLOB,
  template TEXT,        -- JSON for enrollment samples/template (optional)
  device_hash TEXT,
  created_at INTEGER,
  updated_at INTEGER,
  FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  user_id TEXT,
  test_id INTEGER,
  candidate_id INTEGER,
  question_id TEXT,
  status TEXT DEFAULT 'active',
  timestamp INTEGER,
  created_at TEXT,
  updated_at TEXT,
  score REAL,
  verdict TEXT,
  paste_flag INTEGER DEFAULT 0,
  notes TEXT
);
-- backend/schema.sql
CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  name TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS user_scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  session_id TEXT,
  question_id TEXT,
  score INTEGER,
  verdict TEXT,
  meta_json TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  name TEXT,
  email TEXT,
  created_at INTEGER
);

CREATE TABLE IF NOT EXISTS tests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  description TEXT,
  created_at INTEGER
);

CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  text TEXT,
  description TEXT,
  qtype TEXT DEFAULT 'theory',
  created_at INTEGER
);

CREATE TABLE IF NOT EXISTS test_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  test_id INTEGER NOT NULL,
  question_id INTEGER NOT NULL,
  seq INTEGER DEFAULT 1,
  FOREIGN KEY(test_id) REFERENCES tests(id),
  FOREIGN KEY(question_id) REFERENCES questions(id)
);

CREATE TABLE IF NOT EXISTS assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT UNIQUE NOT NULL,
  candidate_id INTEGER,
  test_id INTEGER,
  created_at TEXT,
  FOREIGN KEY(candidate_id) REFERENCES candidates(id),
  FOREIGN KEY(test_id) REFERENCES tests(id)
);

CREATE TABLE IF NOT EXISTS answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  question_id INTEGER,
  answer_text TEXT,
  final_text TEXT,
  created_at TEXT,
  keystroke_session_id TEXT,
  keystroke_score REAL,
  keystroke_verdict TEXT,
  paste_flag INTEGER
);

CREATE TABLE IF NOT EXISTS feature_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  question_id INTEGER,
  meta TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS keystroke_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  event_json TEXT,
  created_at TEXT
);
