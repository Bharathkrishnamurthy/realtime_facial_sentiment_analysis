import sqlite3, json
conn=sqlite3.connect('keystroke.db')
cur=conn.cursor()
rows = cur.execute('PRAGMA table_info(assignments)').fetchall()
print('PRAGMA table_info(assignments):')
for r in rows:
    print(r)
conn.close()
