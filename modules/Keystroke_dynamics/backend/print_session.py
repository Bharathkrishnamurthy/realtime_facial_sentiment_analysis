import sqlite3, json
sid = "283ec01d-188b-4c76-a567-b6422cef8bb4"   # <- your session id
conn = sqlite3.connect('keystroke.db')
conn.row_factory = sqlite3.Row
r = conn.execute('SELECT * FROM sessions WHERE session_id = ?', (sid,)).fetchone()
print(dict(r) if r else "NO SESSION")
conn.close()
