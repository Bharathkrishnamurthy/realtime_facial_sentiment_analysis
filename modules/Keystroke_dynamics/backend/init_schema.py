import sqlite3, os, sys
schema = "schema.sql" if os.path.exists("schema.sql") else "app/schema.sql"
dbpath = "app/keystroke.db"
print("Using schema file:", schema)
print("Creating DB at:", dbpath)
try:
    with open(schema, "r", encoding="utf8") as f:
        sql = f.read()
except Exception as e:
    print("FAILED reading schema:", e)
    sys.exit(2)

# create parent directory if missing
os.makedirs(os.path.dirname(dbpath), exist_ok=True)

# create/overwrite DB
conn = sqlite3.connect(dbpath)
try:
    conn.executescript(sql)
    conn.commit()
    print("Schema executed OK.")
    # quick integrity check
    try:
        r = conn.execute("PRAGMA integrity_check").fetchall()
        print("PRAGMA integrity_check ->", r)
    except Exception as e2:
        print("PRAGMA failed:", e2)
finally:
    conn.close()
