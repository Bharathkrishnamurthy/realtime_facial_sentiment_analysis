import sqlite3, os, sys
src = "app/keystroke.db"
dumpfile = "app/keystroke_dump.sql"
newdb = "app/keystroke_rebuilt.db"
try:
    conn = sqlite3.connect(src)
    with open(dumpfile, "w", encoding="utf8") as f:
        for line in conn.iterdump():
            f.write('%s\n' % line)
    conn.close()
    print("Dump written to", dumpfile)
    if os.path.exists(newdb):
        os.remove(newdb)
    conn2 = sqlite3.connect(newdb)
    cur2 = conn2.cursor()
    sql = open(dumpfile, "r", encoding="utf8").read()
    cur2.executescript(sql)
    conn2.commit()
    conn2.close()
    print("Rebuilt DB created:", newdb)
except Exception as e:
    print("Failed to dump/rebuild:", repr(e))
    sys.exit(1)
