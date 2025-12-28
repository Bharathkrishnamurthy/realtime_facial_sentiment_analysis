# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from .database import init_db, get_conn, now_ts
from .models import SubmitEventsRequest
from .feature_extractor import extract_features
from .matcher import bytes_to_vector, decide_score_and_verdict
from .config import MODEL_VERSION, MIN_ENROLL_CHARS, MIN_ENROLL_KEY_EVENTS
from .interview_routes import router as hr_router
import uuid, sqlite3, json
app = FastAPI(title="Keystroke Biometrics Service")

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize keystroke DB
init_db()

# include HR / interview routes
app.include_router(hr_router)
from .candidate_routes import router as candidate_router
app.include_router(candidate_router)


@app.post("/api/submit_events")
def submit_events(req: SubmitEventsRequest):
    try:
        # --- BEGIN existing handler body (copy everything inside original function) ---
        conn = database.get_conn()
        cur = conn.cursor()

        # 1. Check user exists
        cur.execute("SELECT user_id FROM users WHERE user_id = ?", (req.user_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=400, detail="user not found. create user first via /api/create_user")

        # 2. Prepare basic info
        events = [e.dict() for e in req.events]
        final_text = req.final_text or ""
        chars_typed = len(final_text)
        key_events_count = sum(1 for e in events if e.get("type") in ("keydown", "keyup"))

        # Decide phase if not set
        phase = (req.phase or "").lower()
        if phase not in ("baseline", "test"):
            phase = "baseline" if req.enrollment else "test"

        # 3. Enrollment quality gate
        if req.enrollment:
            if chars_typed < MIN_ENROLL_CHARS or key_events_count < MIN_ENROLL_KEY_EVENTS:
                conn.close()
                return {
                    "status": "too_short",
                    "phase": phase,
                    "reason": "not enough data for enrollment",
                    "min_chars": MIN_ENROLL_CHARS,
                    "min_key_events": MIN_ENROLL_KEY_EVENTS,
                    "chars_typed": chars_typed,
                    "key_events": key_events_count
                }

        # 4. Extract features
        res = extract_features(events)
        vec = res["feature_vector"]
        paste_flag = res["paste_flag"]
        meta = res["meta"]
        ts = now_ts()

        notes_base = {
            "phase": phase,
            "test_id": req.test_id,
            "model_version": MODEL_VERSION,
            "meta": meta,
            "chars_typed": chars_typed,
            "key_events": key_events_count,
        }

        # 5. Enrollment branch
        if req.enrollment:
            blob = vec.tobytes()
            cur.execute(
                "INSERT INTO profiles(user_id, embedding, device_hash, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (req.user_id, sqlite3.Binary(blob), req.device_info or "", ts, ts),
            )
            conn.commit()

            session_id = str(uuid.uuid4())
            notes = json.dumps({**notes_base, "raw_score": 1.0})
            cur.execute(
                "INSERT INTO sessions(session_id, user_id, question_id, timestamp, score, verdict, paste_flag, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    req.user_id,
                    req.question_id or "",
                    ts,
                    1.0,
                    "enrolled",
                    int(paste_flag),
                    notes,
                ),
            )
            conn.commit()
            conn.close()
            return {
                "status": "enrolled",
                "phase": phase,
                "meta": meta
            }

        # 6. Verification branch
        cur.execute("SELECT embedding FROM profiles WHERE user_id = ?", (req.user_id,))
        rows = cur.fetchall()
        templates = [bytes_to_vector(r[0]) for r in rows if r and r[0]]

        verdict_res = decide_score_and_verdict(vec, templates, paste_flag)

        session_id = str(uuid.uuid4())
        notes = json.dumps({**notes_base, "raw_score": verdict_res["score"]})
        cur.execute(
            "INSERT INTO sessions(session_id, user_id, question_id, timestamp, score, verdict, paste_flag, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                req.user_id,
                req.question_id or "",
                ts,
                verdict_res["score"],
                verdict_res["verdict"],
                int(paste_flag),
                notes,
            ),
        )
        conn.commit()
        conn.close()

        return {
            "score": verdict_res["score"],
            "verdict": verdict_res["verdict"],
            "paste_flag": paste_flag,
            "meta": meta,
            "phase": phase,
            "session_id": session_id
        }
        # --- END existing handler body ---
    except Exception as exc:
        import traceback, sys
        tb = traceback.format_exc()
        # write a short log file so you can inspect it
        with open("submit_events_error.log", "w", encoding="utf-8") as f:
            f.write(tb)
        # return error details in HTTP response (DEBUG only!)
        raise HTTPException(status_code=500, detail={"error": str(exc), "traceback": tb.splitlines()[-20:]})
@app.post("/api/create_user")
def create_user():
    """
    Create a new user_id and persist to users table.
    Returns: { "user_id": "<uuid>" }
    """
    user_id = str(uuid.uuid4())
    ts = now_ts()
    conn = database.get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO users(user_id, created_at) VALUES (?, ?)", (user_id, ts))
    conn.commit()
    conn.close()
    return {"user_id": user_id}
