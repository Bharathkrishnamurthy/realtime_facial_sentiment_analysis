import sqlite3

conn = sqlite3.connect("keystroke.db")
cur = conn.cursor()

queries = [
    ("INSERT INTO questions (id, text) VALUES (1001, 'Please write: my keyboard test contains commas, periods. does it work? yes!');"),
    ("INSERT INTO questions (id, text) VALUES (1002, 'Type: AbCdEFg 12345');"),
    ("INSERT INTO questions (id, text) VALUES (1003, 'The quick brown fox jumps over the lazy dog.');"),
    ("INSERT INTO questions (id, text) VALUES (1004, 'Symbols: ! @ # $ % ^ & * ( ) - _ = + [ ] { } ; : '' \" , . < > / ? \\\\ | ` ~');"),
    ("INSERT INTO questions (id, text) VALUES (1005, 'Numbers: 0123456789. Try math 25+5=30; 3.14 approx.');"),
    ("INSERT INTO questions (id, text) VALUES (1006, 'Please type a two-line response (press Enter once) to demonstrate Enter key usage.');"),
    ("INSERT OR IGNORE INTO tests (id, name) VALUES (99, 'Demo Coverage Test');"),
    ("INSERT OR IGNORE INTO test_questions (id, test_id, question_id, seq) VALUES (1001, 99, 1001, 1);"),
    ("INSERT OR IGNORE INTO test_questions (id, test_id, question_id, seq) VALUES (1002, 99, 1002, 2);"),
    ("INSERT OR IGNORE INTO test_questions (id, test_id, question_id, seq) VALUES (1003, 99, 1003, 3);"),
    ("INSERT OR IGNORE INTO test_questions (id, test_id, question_id, seq) VALUES (1004, 99, 1004, 4);"),
    ("INSERT OR IGNORE INTO test_questions (id, test_id, question_id, seq) VALUES (1005, 99, 1005, 5);"),
    ("INSERT OR IGNORE INTO test_questions (id, test_id, question_id, seq) VALUES (1006, 99, 1006, 6);"),
]

for q in queries:
    try:
        cur.execute(q)
    except Exception as e:
        print("Skipping:", e)

conn.commit()
conn.close()

print("Questions inserted successfully!")
