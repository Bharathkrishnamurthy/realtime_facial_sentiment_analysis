# backend/app/user_routes.py
from fastapi import APIRouter, Request, HTTPException
import uuid
from .database import get_conn
from sqlite3 import OperationalError

router = APIRouter()

@router.post("/api/create_user")
async def create_user(req: Request):
    """
    Create a simple user record and return user_id and name.
    Expects optional JSON body: { "name": "Jayashree" }
    """
    try:
        data = await req.json()
    except Exception:
        data = {}

    name = (data.get("name") or "").strip() if isinstance(data, dict) else ""
    user_id = str(uuid.uuid4())

    # insert into users table
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (user_id, name, created_at) VALUES (?, ?, datetime('now'))",
            (user_id, name or None),
        )
        conn.commit()
    except OperationalError as oe:
        # likely table not found or DB not initialized
        raise HTTPException(status_code=500, detail=f"DB error: {oe}")
    finally:
        if conn:
            conn.close()

    return {"user_id": user_id, "name": name}
