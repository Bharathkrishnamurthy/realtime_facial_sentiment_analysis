# fix_db_and_insert.py
import sqlite3, time, os, traceback

DB = os.path.join(os.path.dirname(__file__), "keystroke.db")
token = "fe5cf222-b59a-41ca-b30a-f7b7e32b3de2"

def has_table(cur, name):
    r = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone()
    return r is not None

def column_names(cur, table):
    try:
        rows = cur.execute(f"PRAGMA table_info('{table}')").fetchall()
        return [r[1] for r in rows]
    except Exception:
        return []

conn = sqlite3.connect(DB)
cur = conn.cursor()

try:
    print("DB path:", DB)
    print("Existing tables:", [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])

    # Ensure questions table exists
    if not has_table(cur, "questions"):
        print("Creating table 'questions'")
        cur.execute("""CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text TEXT
                    )""")
        conn.commit()

    # Ensure test_questions table exists (basic columns)
    if not has_table(cur, "test_questions"):
        print("Creating table 'test_questions'")
        cur.execute("""CREATE TABLE IF NOT EXISTS test_questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id INTEGER,
                        question_id INTEGER
                    )""")
        conn.commit()

    # If seq column missing, add it
    cols = column_names(cur, "test_questions")
    if "seq" not in cols:
        print("Adding missing 'seq' column to test_questions")
        cur.execute("ALTER TABLE test_questions ADD COLUMN seq INTEGER DEFAULT 1")
        conn.commit()
    else:
        print("'seq' column already present in test_questions")

    # Ensure assignments table exists (basic)
    if not has_table(cur, "assignments"):
        print("Creating table 'assignments'")
        cur.execute("""CREATE TABLE IF NOT EXISTS assignments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token TEXT UNIQUE,
                        candidate_id INTEGER,
                        test_id INTEGER,
                        created_at TEXT
                    )""")
        conn.commit()

    # Insert sample question (id=1 or preserve existing)
    cur.execute("INSERT OR IGNORE INTO questions (id, text) VALUES (?, ?)", (1, "Sample question text for enrollment"))
    conn.commit()
    print("Ensured sample question (id=1) exists")

    # Insert test_question linking test_id=1 -> question_id=1
    cur.execute("INSERT OR IGNORE INTO test_questions (id, test_id, question_id, seq) VALUES (?, ?, ?, ?)", (1, 1, 1, 1))
    conn.commit()
    print("Ensured test_questions linking test 1 -> question 1")

    # Insert assignment for demo token
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT OR IGNORE INTO assignments (token, candidate_id, test_id, created_at) VALUES (?, ?, ?, ?)",
                (token, 1, 1, now))
    conn.commit()

    # Show the inserted assignment row
    row = cur.execute("SELECT * FROM assignments WHERE token=?", (token,)).fetchone()
    print("Assignment row:", dict(row) if row else "not found")

    # Final table overview
    print("Final tables:", [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
    print("test_questions columns:", column_names(cur, "test_questions"))

except Exception as e:
    print("ERROR:", e)
    traceback.print_exc()
finally:
    conn.close()
