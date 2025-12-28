import app.database as database
import sqlite3, json
print("app.database module file:", database.__file__)
conn = database.get_db()
print("PRAGMA database_list ->", conn.execute("PRAGMA database_list").fetchall())
conn.close()
