import sqlite3, sys
p = "app/keystroke.db"
try:
    conn = sqlite3.connect(p)
    cur = conn.cursor()
    res = cur.execute("PRAGMA integrity_check;").fetchall()
    print("PRAGMA integrity_check result:", res)
    conn.close()
except Exception as e:
    print("ERROR running integrity_check:", repr(e))
    sys.exit(1)
