import sqlite3, os, sys
src = "app/keystroke.db"
dst = "app/keystroke_repaired.db"
try:
    conn = sqlite3.connect(src)
    cur = conn.cursor()
    print("integrity_check:", cur.execute("PRAGMA integrity_check;").fetchone())
    print("Attempting VACUUM INTO", dst)
    cur.execute("VACUUM INTO '" + dst.replace("'", "''") + "';")
    conn.close()
    if os.path.exists(dst):
        print("VACUUM INTO succeeded. New DB:", dst)
    else:
        print("VACUUM INTO did not create file.")
except Exception as e:
    print("VACUUM INTO failed:", repr(e))
    sys.exit(1)
