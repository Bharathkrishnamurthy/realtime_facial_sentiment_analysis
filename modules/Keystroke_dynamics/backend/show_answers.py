import sqlite3
conn = sqlite3.connect('keystroke.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
print("Recent answers:")
for r in cur.execute("SELECT id, session_id, question_id, final_text, created_at FROM answers ORDER BY id DESC LIMIT 10"):
    print(dict(r))
conn.close()
