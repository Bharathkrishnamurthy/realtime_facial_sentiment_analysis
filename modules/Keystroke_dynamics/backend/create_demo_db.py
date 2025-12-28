# backend/create_demo_db.py
import sqlite3, os, shutil, time
from datetime import datetime

BASE = os.path.dirname(__file__)
DB = os.path.join(BASE, "app", "keystroke.db")
SCHEMA = os.path.join(BASE, "schema.sql")

def backup_db():
    if os.path.exists(DB):
        bak = DB + ".backup_" + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(DB, bak)
        print("Backed up", DB, "->", bak)

def create_db_and_demo():
    if not os.path.exists(SCHEMA):
        raise FileNotFoundError("schema.sql not found at " + SCHEMA)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    with open(SCHEMA, 'r', encoding='utf8') as f:
        cur.executescript(f.read())
    conn.commit()

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    # Insert demo test and coverage questions (IDs chosen stable)
    cur.execute("INSERT OR IGNORE INTO tests (id, name, description) VALUES (1, ?, ?)", ("Demo Coverage Test", "Auto demo test"))
    demo_qs = [
        (1001, "Please write: my keyboard test contains commas, periods. does it work? yes!"),
        (1002, "Type: AbCdEFg 12345"),
        (1003, "The quick brown fox jumps over the lazy dog."),
        (1004, "Symbols: ! @ # $ % ^ & * ( ) - _ = + [ ] { } ; : ' \" , . < > / ? \\ | ` ~"),
        (1005, "Numbers: 0123456789. Try math 25+5=30; 3.14 approx."),
        (1006, "Please type a two-line response (press Enter once) to demonstrate Enter key usage.")
    ]
    for qid, text in demo_qs:
        cur.execute("INSERT OR IGNORE INTO questions (id, text, description) VALUES (?, ?, ?)", (qid, text, "coverage"))
        cur.execute("INSERT OR IGNORE INTO test_questions (test_id, question_id, seq) VALUES (?, ?, ?)", (1, qid, qid - 1000))
    # Insert demo candidate + assignments token
    cur.execute("INSERT OR IGNORE INTO candidates (id, name, email) VALUES (1, ?, ?)", ("Demo Candidate", "demo@example.com"))
    token = "fe5cf222-b59a-41ca-b30a-f7b7e32b3de2"
    cur.execute("INSERT OR IGNORE INTO assignments (id, token, candidate_id, test_id, created_at) VALUES (1, ?, ?, ?, ?)",
                (token, 1, 1, now))
    conn.commit()
    conn.close()
    print("Created fresh DB and demo rows at", DB)
    print("Demo assignment token:", token)

if __name__ == "__main__":
    backup_db()
    create_db_and_demo()
