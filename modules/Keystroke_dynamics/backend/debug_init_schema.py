# debug_init_schema.py
import sqlite3, traceback, importlib, app, os, sys
# import module as a module object without running top-level init by re-reading file text
p = "app/interview_routes.py"
print("Reading interview_routes.py from", p)
text = open(p, "r", encoding="utf8").read()

# find SCHEMA_SQL assignment in that file (best-effort)
start = text.find("SCHEMA_SQL")
if start==-1:
    print("SCHEMA_SQL not found by simple search - will import module and inspect attributes")
    # import the module normally (but we previously patched main.py to not auto-run init; safe)
    import importlib
    m = importlib.import_module("app.interview_routes")
    if hasattr(m, "SCHEMA_SQL"):
        s = getattr(m, "SCHEMA_SQL")
        print("SCHEMA_SQL size (chars):", len(s))
        print("first 800 chars:\\n", s[:800])
    else:
        print("module has no SCHEMA_SQL attribute")
else:
    #attempt to parse assignment naively
    print("SCHEMA_SQL appears in file; printing first 800 chars of file containing it")
    print(text[start:start+800])

# Now attempt to execute SCHEMA_SQL (if present) against DB and catch exact exception
try:
    import app.database as database
    conn = database.get_db()
    cur = conn.cursor()
    if 'm' not in locals():
        import importlib
        m = importlib.import_module("app.interview_routes")
    if hasattr(m, "SCHEMA_SQL"):
        sql = getattr(m, "SCHEMA_SQL")
        print("\\nAttempting to executescript(...) of SCHEMA_SQL now; this will be trapped.")
        try:
            cur.executescript(sql)
            conn.commit()
            print("executescript succeeded.")
        except Exception as e:
            print("executescript raised:", repr(e))
            tb = traceback.format_exc()
            print(tb)
            # show snippet around where SQL might fail (best-effort)
            print("\\nSQL snippet (first 2000 chars):\\n", (sql[:2000] if sql else "<empty>"))
    else:
        print("No SCHEMA_SQL to execute.")
    conn.close()
except Exception as e:
    print("Error opening DB or running SQL:", repr(e))
    traceback.print_exc()
    sys.exit(1)
