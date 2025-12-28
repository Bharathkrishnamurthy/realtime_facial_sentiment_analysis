import app.session_service as ss, app.database as db
conn = db.get_db()
try:
    print("Calling create_session_for_token(...)")
    print(ss.create_session_for_token(conn, "fe5cf222-b59a-41ca-b30a-f7b7e32b3de2"))
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    conn.close()
