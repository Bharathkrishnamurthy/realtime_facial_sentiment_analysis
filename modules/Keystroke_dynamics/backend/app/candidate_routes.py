# app/candidate_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import app.database as database
import app.session_service as session_service
from app.models import Event
import logging

logger = logging.getLogger("keystroke_candidate")
router = APIRouter(prefix="/candidate", tags=["candidate"])


class StartRequest(BaseModel):
    token: str


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: int
    final_text: Optional[str] = ""
    events: List[Event] = []


class FinishRequest(BaseModel):
    session_id: str


@router.post("/start")
def start_test(req: StartRequest):
    """
    Create a session for the given token and return questions.
    Demo-friendly fallback:
      - If session_service.create_session_for_token returns nothing (invalid token),
        create a lightweight session row in the DB so the UI can continue.
      - If the test exists, fetch questions as before; otherwise return a simple default question.
    """
    db = None
    try:
        db = database.get_conn()

        # Try normal path (session_service may validate token)
        try:
            session_id, test_id = session_service.create_session_for_token(db, req.token)
        except Exception:
            # don't fail here — log and fall through to demo fallback
            session_id, test_id = None, None

        # If not created by session_service (invalid token), create a lightweight session row
        if not session_id:
            import uuid, time
            session_id = str(uuid.uuid4())
            # insert a session row compatible with your schema (adjust columns if your schema differs)
            try:
                # created_at using unix timestamp; adjust if your schema uses datetime strings
                created_at = int(time.time())
                db.execute(
                    "INSERT INTO sessions (session_id, token, status, created_at) VALUES (?, ?, ?, ?)",
                    (session_id, req.token, "active", created_at),
                )
                db.commit()
            except Exception:
                # If schema differs, try a minimal insert with only session_id if possible
                try:
                    db.execute("INSERT INTO sessions (session_id) VALUES (?)", (session_id,))
                    db.commit()
                except Exception:
                    # If we can't persist, still return a generated session_id (non-persistent)
                    pass

        # Try to fetch questions for test_id if available; otherwise return a default question set
        questions = []
        if test_id:
            try:
                questions = session_service.get_questions_for_test(db, test_id)
            except Exception:
                questions = []
        if not questions:
            questions = [{"question_id": 1, "text": "Please introduce yourself."}]

        return {"status": "ok", "session_id": session_id, "test_id": test_id, "questions": questions}
    except Exception as e:
        logger.exception("start_test failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if db:
                db.close()
        except Exception:
            pass



@router.post("/submit_answer")
def submit_answer(req: SubmitAnswerRequest):
    """
    Save the candidate's answer and keystroke events.
    """
    db = None
    try:
        db = database.get_conn()
        s = db.execute("SELECT * FROM sessions WHERE session_id = ? LIMIT 1", (req.session_id,)).fetchone()
        if not s:
            raise HTTPException(status_code=404, detail="session not found")
        # mark started if needed
        try:
            db.execute(
                "UPDATE sessions SET started_at = COALESCE(started_at, datetime('now')), "
                "status = COALESCE(status, 'active') WHERE session_id = ?",
                (req.session_id,),
            )
            db.commit()
        except Exception:
            # do not fail if update fails
            logger.debug("could not update session start status", exc_info=True)

        # Save answer and biometrics
        session_service.save_answer_and_biometrics(
            db,
            req.session_id,
            req.question_id,
            req.final_text or "",
            [e.dict() for e in req.events] if req.events else [],
        )
        return {"status": "ok", "note": "features extracted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("submit_answer failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if db:
                db.close()
        except Exception:
            pass


@router.post("/finish")
def finish_test(req: FinishRequest):
    """
    Finalize the session and compute score/verdict using session_service.
    """
    db = None
    try:
        db = database.get_conn()
        s = db.execute("SELECT * FROM sessions WHERE session_id = ? LIMIT 1", (req.session_id,)).fetchone()
        if not s:
            raise HTTPException(status_code=404, detail="session not found")
        score, authenticity = session_service.finish_session(db, req.session_id)
        return {"status": "ok", "session_id": req.session_id, "score": score, "authenticity": authenticity}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("finish_test failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if db:
                db.close()
        except Exception:
            pass
