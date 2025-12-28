# app/interviewer_routes.py
from fastapi import APIRouter, HTTPException
import app.database as database
import json, logging
from collections import Counter

router = APIRouter(prefix="/interviewer", tags=["interviewer"])
logger = logging.getLogger("keystroke_interviewer")

@router.get("/summary")
def get_summary(limit: int = 50):
    db = database.database.get_conn()
    try:
        rows = db.execute("SELECT session_id, candidate_id, test_id, started_at, finished_at, status FROM sessions ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
        sessions = []
        for r in rows:
            try:
                sessions.append({k: r[k] for k in r.keys()})
            except Exception:
                sessions.append(tuple(r))
        total_sessions = db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        total_answers = 0
        try:
            total_answers = db.execute("SELECT COUNT(*) FROM answers").fetchone()[0]
        except Exception:
            total_answers = 0
        return {"total_sessions": total_sessions, "total_answers": total_answers, "sessions": sessions}
    finally:
        try: db.close()
        except: pass

@router.get("/session/{session_id}/keystrokes")
def session_keystrokes(session_id: str, limit: int = 5000):
    db = database.database.get_conn()
    try:
        rows = db.execute("SELECT event_json, created_at FROM keystroke_events WHERE session_id = ? ORDER BY id ASC LIMIT ?", (session_id, limit)).fetchall()
        out = []
        for r in rows:
            try:
                e = json.loads(r[0])
            except Exception:
                e = r[0]
            out.append({"event": e, "created_at": r[1]})
        return {"session_id": session_id, "events": out}
    finally:
        try: db.close()
        except: pass

@router.get("/session/{session_id}/summary")
def session_summary(session_id: str):
    """
    Return aggregated summary (counts, paste incidents, blur count) for a session.
    """
    db = database.database.get_conn()
    try:
        rows = db.execute("SELECT event_json FROM keystroke_events WHERE session_id = ?", (session_id,)).fetchall()
        paste_incidents = 0
        blur_incidents = 0
        total_events = 0
        for r in rows:
            try:
                e = json.loads(r[0])
            except Exception:
                e = r[0]
            total_events += 1
            if isinstance(e, dict):
                if e.get("type") == "paste" or e.get("clipboardLength"):
                    paste_incidents += 1
                if e.get("type") == "blur":
                    blur_incidents += 1
        return {"session_id": session_id, "total_event_rows": total_events, "paste_incidents": paste_incidents, "blur_incidents": blur_incidents}
    finally:
        try: db.close()
        except: pass

@router.get("/profile/{candidate_id}")
def profile_for_candidate(candidate_id: int):
    db = database.database.get_conn()
    try:
        row = db.execute("SELECT id, user_id, template, created_at, updated_at, embedding IS NOT NULL as has_embedding FROM profiles WHERE user_id = ? OR id = ? LIMIT 1",
                         (str(candidate_id), candidate_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="profile not found")
        try:
            tpl_json = row["template"]
            pid = row["id"]
            user_id = row["user_id"]
            created = row.get("created_at")
            updated = row.get("updated_at")
            has_emb = bool(row.get("has_embedding", False))
        except Exception:
            pid, user_id, tpl_json = row[0], row[1], row[2]
            created = row[3] if len(row) > 3 else None
            updated = row[4] if len(row) > 4 else None
            has_emb = False
        try:
            tpl = json.loads(tpl_json) if tpl_json else None
        except Exception:
            tpl = None
        return {"id": pid, "user_id": user_id, "template": tpl, "has_embedding": has_emb, "created_at": created, "updated_at": updated}
    finally:
        try: db.close()
        except: pass
