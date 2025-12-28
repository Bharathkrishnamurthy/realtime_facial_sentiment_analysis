import app.database as database, sqlite3
conn = database.get_db()
conn.row_factory = sqlite3.Row
cur = conn.cursor()
print("Recent sessions:")
for r in cur.execute("SELECT * FROM sessions ORDER BY rowid DESC LIMIT 10").fetchall():
    print(dict(r))
print("\nRecent answers:")
try:
    for r in cur.execute("SELECT * FROM answers ORDER BY rowid DESC LIMIT 10").fetchall():
        try:
            print(dict(r))
        except:
            print(r)
except Exception as e:
    print("answers table error:", e)
print("\nRecent feature_logs:")
try:
    for r in cur.execute("SELECT * FROM feature_logs ORDER BY rowid DESC LIMIT 10").fetchall():
        try:
            print(dict(r))
        except:
            print(r)
except Exception as e:
    print("feature_logs table error:", e)
conn.close()
