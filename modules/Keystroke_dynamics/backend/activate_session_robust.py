import sqlite3, time, sys, json, os

if len(sys.argv) < 2:
    print("Usage: python activate_session_robust.py <SESSION_ID>")
    sys.exit(2)

sid = sys.argv[1]
candidates = ["app/keystroke.db", "keystroke.db"]

def try_open(dbpath):
    if not os.path.exists(dbpath):
        return None
    try:
        conn = sqlite3.connect(dbpath)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print("open error", dbpath, e)
        return None

found = False
for dbpath in candidates:
    conn = try_open(dbpath)
    if not conn:
        continue
    cur = conn.cursor()
    # check if this DB has the session
    try:
        r = cur.execute("SELECT * FROM sessions WHERE session_id = ?", (sid,)).fetchone()
    except Exception as e:
        # sessions table might have different name/schema
        r = None
    if not r:
        conn.close()
        continue

    found = True
    print("Using DB:", dbpath)
    # list columns for sessions
    cols = [c[1] for c in cur.execute("PRAGMA table_info(sessions)").fetchall()]
    print("sessions columns:", cols)

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    updated = False

    # try to update common schema: status + started_at
    if "status" in cols and ("started_at" in cols or "started" in cols or "created_at" in cols):
        started_col = "started_at" if "started_at" in cols else ("started" if "started" in cols else "created_at")
        try:
            cur.execute(f"UPDATE sessions SET status = ?, {started_col} = ? WHERE session_id = ?", ("active", now, sid))
            conn.commit()
            updated = True
        except Exception as e:
            print("update attempt 1 failed:", e)

    # fallback: timestamp integer column
    if not updated and "timestamp" in cols:
        try:
            cur.execute("UPDATE sessions SET timestamp = ? WHERE session_id = ?", (int(time.time()), sid))
            conn.commit()
            updated = True
        except Exception as e:
            print("update attempt 2 failed:", e)

    # fallback: status only
    if not updated and "status" in cols:
        try:
            cur.execute("UPDATE sessions SET status = ? WHERE session_id = ?", ("active", sid))
            conn.commit()
            updated = True
        except Exception as e:
            print("update attempt 3 failed:", e)

    # fallback: update any column that looks like created/updated names (best-effort)
    if not updated:
        for candidate_col in ("created_at","created","started","started_at","timestamp"):
            if candidate_col in cols:
                try:
                    if candidate_col == "timestamp":
                        cur.execute(f"UPDATE sessions SET {candidate_col} = ? WHERE session_id = ?", (int(time.time()), sid))
                    else:
                        cur.execute(f"UPDATE sessions SET {candidate_col} = ? WHERE session_id = ?", (now, sid))
                    conn.commit()
                    updated = True
                    break
                except Exception:
                    pass

    # print result row robustly
    r2 = cur.execute("SELECT * FROM sessions WHERE session_id = ?", (sid,)).fetchone()
    if not r2:
        print("SESSION ROW disappeared after update? (unexpected)")
    else:
        try:
            print("Session after update:", dict(r2))
        except Exception:
            # fallback to mapping via PRAGMA
            cols = [c[0] for c in cur.execute("PRAGMA table_info(sessions)").fetchall()]
            print("Session after update:", {cols[i]: r2[i] for i in range(len(cols))})
    conn.close()
    break

if not found:
    print("SESSION ID not found in candidate DB files:", candidates)
    sys.exit(1)
