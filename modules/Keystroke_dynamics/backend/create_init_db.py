import sqlite3, os, sys, traceback

# prefer ./schema.sql then ./app/schema.sql
schema_candidates = ["schema.sql", "app/schema.sql"]
schema = None
for s in schema_candidates:
    if os.path.exists(s):
        schema = s
        break

if not schema:
    print("ERROR: no schema.sql found. Checked:", schema_candidates)
    sys.exit(2)

with open(schema, "r", encoding="utf8") as f:
    sql = f.read()

out_db = os.path.join("app","keystroke_new.db")
# ensure folder
os.makedirs(os.path.dirname(out_db), exist_ok=True)

# If file exists, back it up
if os.path.exists(out_db):
    bak = out_db + ".bak_" + __import__("time").strftime("%Y%m%dT%H%M%S", __import__("time").gmtime())
    os.rename(out_db, bak)
    print("Backed up existing", out_db, "->", bak)

print("Creating new DB at:", out_db, "using schema:", schema)
try:
    conn = sqlite3.connect(out_db)
    cur = conn.cursor()
    cur.executescript(sql)
    conn.commit()
    # verify integrity
    res = cur.execute("PRAGMA integrity_check").fetchall()
    print("PRAGMA integrity_check ->", res)
    conn.close()
    if res and res[0][0] == "ok":
        print("SUCCESS: fresh DB created OK.")
        sys.exit(0)
    else:
        print("WARNING: integrity_check returned:", res)
        sys.exit(1)
except Exception as e:
    print("ERROR while creating DB:", repr(e))
    traceback.print_exc()
    # remove partially created DB to avoid confusion
    try:
        if os.path.exists(out_db):
            os.remove(out_db)
            print("Removed incomplete DB file:", out_db)
    except Exception:
        pass
    sys.exit(3)
