import app.database as database
import sqlite3
conn = database.get_db()
print("DB LIST:", conn.execute("PRAGMA database_list").fetchall())
conn.close()
