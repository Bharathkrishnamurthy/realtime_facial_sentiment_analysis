# check_assignment.py
import sqlite3, json
conn = sqlite3.connect("keystroke.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
r = cur.execute("SELECT * FROM assignments WHERE token=?", ("fe5cf222-b59a-41ca-b30a-f7b7e32b3de2",)).fetchone()
print(dict(r) if r else "NO ROW FOUND")
conn.close()
