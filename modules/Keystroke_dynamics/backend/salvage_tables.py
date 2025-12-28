import sqlite3, sys, os, traceback
src = "app/keystroke.db"
dst = "app/keystroke_salvaged.db"
try:
    s = sqlite3.connect(src)
    s.row_factory = sqlite3.Row
    cur = s.cursor()
    # get table names
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
    print("Found tables:", tables)
    # create new DB
    if os.path.exists(dst): os.remove(dst)
    d = sqlite3.connect(dst)
    dcur = d.cursor()
    for t in tables:
        try:
            # get table schema
            schema = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()
            if not schema or not schema[0]:
                print("Skipping table (no schema):", t); continue
            print("Creating table in new DB:", t)
            dcur.execute(schema[0])
            # copy rows by selecting in small batches
            rows = cur.execute("SELECT * FROM " + t).fetchall()
            if not rows:
                print("No rows for", t); continue
            cols = [c[0] for c in cur.execute("PRAGMA table_info(%s)"%t).fetchall()]
            placeholders = ",".join(["?"]*len(cols))
            insert_sql = "INSERT INTO %s (%s) VALUES (%s)" % (t, ",".join(cols), placeholders)
            for r in rows:
                try:
                    dcur.execute(insert_sql, tuple(r[col] for col in cols))
                except Exception as ex:
                    # skip problematic row
                    print("Skipped row in", t, "due to", ex)
            d.commit()
            print("Copied table", t)
        except Exception as e:
            print("Error copying table", t, ":", repr(e))
    s.close(); d.close()
    print("Salvage complete. New DB:", dst)
except Exception as e:
    print("Salvage failed:", repr(e))
    traceback.print_exc()
    sys.exit(1)
