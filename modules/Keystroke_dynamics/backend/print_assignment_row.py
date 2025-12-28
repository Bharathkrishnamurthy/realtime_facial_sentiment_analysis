import sqlite3, json
conn = sqlite3.connect('keystroke.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
token = 'fe5cf222-b59a-41ca-b30a-f7b7e32b3de2'
r = cur.execute('SELECT * FROM assignments WHERE token = ?', (token,)).fetchone()
if not r:
    print('NO ROW FOUND for token', token)
else:
    cols = [c[0] for c in cur.execute("PRAGMA table_info(assignments)").fetchall()]
    out = {cols[i]: r[i] for i in range(len(cols))}
    print('Assignment row:', out)
conn.close()
