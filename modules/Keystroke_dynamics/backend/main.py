# File: app/main.py
from .user_routes import router as user_router
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from .database import init_db, get_conn, now_ts
from .feature_extractor import extract_features
from .matcher import bytes_to_vector, decide_score_and_verdict
from .config import MODEL_VERSION, MIN_ENROLL_CHARS, MIN_ENROLL_KEY_EVENTS

import uuid, sqlite3, json, traceback, logging
from pathlib import Path
from typing import Dict, Any
# --- extra table to persist every sample for analysis / evaluation ---
SAMPLES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS keystroke_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  session_id TEXT,
  phase TEXT,
  enrollment INTEGER,
  question_id TEXT,
  events_json TEXT,
  meta_json TEXT,
  score REAL,
  verdict TEXT,
  paste_flag INTEGER,
  created_at INTEGER
);
"""
TEMPLATES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS keystroke_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  template_json TEXT NOT NULL,
  created_at INTEGER
);
"""
def ensure_templates_table():
    """
    Table that stores front-end templates per user (for your demo UI).
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(TEMPLATES_TABLE_SQL)
    conn.commit()
    conn.close()

def ensure_samples_table():
  """
  Make sure keystroke_samples table exists.
  Uses existing get_conn() so it stays compatible with your DB layer.
  """
  conn = get_conn()
  cur = conn.cursor()
  cur.execute(SAMPLES_TABLE_SQL)
  conn.commit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("keystroke")

app = FastAPI(title="Keystroke Biometrics Service")

@app.on_event("startup")
def startup_event():
    init_db()
    ensure_samples_table()
    ensure_templates_table()

# include user router (preferably before other routers or after)
app.include_router(user_router)

# --- Serve static demo UI -----------------------------------------------
static_dir = Path(__file__).resolve().parent / "static"
# ensure static directory exists (you already had files there)
static_dir.mkdir(parents=True, exist_ok=True)

# mount static files under /static
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# explicit route to serve demo html
@app.get("/keystroke_demo.html")
def serve_demo():
    demo_file = static_dir / "keystroke_demo.html"
    if demo_file.exists():
        return FileResponse(str(demo_file), media_type="text/html")
    raise HTTPException(status_code=404, detail="Demo HTML not found")

# also allow direct /static/keystroke_demo.html browser accesses to succeed
@app.get("/static/keystroke_demo.html")
def serve_demo_static():
    return serve_demo()
# ------------------------------------------------------------------------

@app.get("/")
def root():
    return RedirectResponse(url="/keystroke_demo.html")

# Add CORS middleware (allow local dev origins)
origins = [
    "http://127.0.0.1:8000",   # where you might serve the demo HTML
    "http://localhost:8000",
    "http://127.0.0.1:9000",   # backend itself (if needed)
    "http://localhost:9000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize DB (keeps your existing DB init behavior)
init_db()

# include routers if present (fail-safe)
try:
    from .interview_routes import router as hr_router
    app.include_router(hr_router)
except Exception as e:
    logger.info("interview_routes not loaded: %s", e)

try:
    from .candidate_routes import router as candidate_router
    app.include_router(candidate_router)
except Exception as e:
    logger.info("candidate_routes not loaded: %s", e)


# --- create_user (no name) - paste this AFTER app = FastAPI() ---
from fastapi import Request, HTTPException
import uuid
import time
from .database import get_conn  # uses your existing database.py

@app.post("/api/create_user")
async def create_user_quick(req: Request):
    """
    Quick endpoint to create a user and persist into SQLite.
    This version DOES NOT store a name (keeps compatibility with current DB).
    """
    user_id = str(uuid.uuid4())
    created_at = int(time.time())

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        # Ensure 'users' table exists with the known schema (no 'name' column)
        cur.execute("""
          CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at INTEGER
          )
        """)
        cur.execute("INSERT INTO users (user_id, created_at) VALUES (?, ?)", (user_id, created_at))
        conn.commit()
    except Exception as e:
        # return clear message for debugging in the UI if needed
        raise HTTPException(status_code=500, detail=f"DB error: {e}")
    finally:
        if conn:
            conn.close()

    return {"user_id": user_id}
# --- end create_user ---

@app.post("/api/save_template")
async def api_save_template(request: Request):
    """
    Store a front-end template (the JSON built in keystroke_demo.html) into SQLite.
    """
    body = await request.json()
    user_id = body.get("user_id")
    template = body.get("template")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    if template is None:
        raise HTTPException(status_code=400, detail="template required")

    try:
        conn = get_conn()
        cur = conn.cursor()
        ensure_templates_table()
        cur.execute(
            """
            INSERT INTO keystroke_templates (user_id, template_json, created_at)
            VALUES (?, ?, ?)
            """,
            (user_id, json.dumps(template), now_ts()),
        )
        conn.commit()
        conn.close()
        return {"ok": True}
    except Exception as e:
        logger.exception("save_template failed: %s", e)
        raise HTTPException(status_code=500, detail=f"save_template error: {e}")


@app.get("/api/templates")
async def api_list_templates(user_id: str):
    """
    Return all templates for a user (latest first) for the demo UI.
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        ensure_templates_table()
        cur.execute(
            """
            SELECT template_json
            FROM keystroke_templates
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
        templates = [json.loads(r[0]) for r in rows]
        return templates
    except Exception as e:
        logger.exception("templates query failed: %s", e)
        raise HTTPException(status_code=500, detail=f"templates error: {e}")

@app.post("/api/submit_events")
async def submit_events(request: Request):
    try:
        body = await request.json()

        user_id = body.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")

        question_id = body.get("question_id", "")
        enrollment = bool(body.get("enrollment", False))
        final_text = body.get("final_text", "") or ""
        events = body.get("events", []) or []
        device_info = body.get("device_info", "")
        phase_in = (body.get("phase", "") or "").lower()
        test_id = body.get("test_id", None)

        conn = get_conn()
        cur = conn.cursor()

        # check user exists
        cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="user not found. create user first via /api/create_user")

        chars_typed = len(str(final_text))
        key_events_count = sum(1 for e in events if e.get("type") in ("keydown", "keyup"))

        phase = phase_in if phase_in in ("baseline", "test") else ("baseline" if enrollment else "test")

        # enrollment gating
        if enrollment:
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

        # feature extraction
        res = extract_features(events)
        # extract_features may return a dict or an object; be defensive
        if isinstance(res, dict):
            vec = res.get("feature_vector")
            paste_flag = bool(res.get("paste_flag", False))
            meta = res.get("meta", {}) or {}
        else:
            # fallback: try attribute access
            vec = getattr(res, "feature_vector", None)
            paste_flag = bool(getattr(res, "paste_flag", False))
            meta = getattr(res, "meta", {}) or {}
        # helper: store raw events + meta for later experiments (3 vs 9 features)
        ts = now_ts()

        def _store_raw_sample(session_id_val, phase_val, verdict_label, score_val):
            """
            Insert one row into keystroke_samples.
            Uses the same cursor/connection as other inserts in this request.
            """
            try:
                cur.execute(
                    """
                    INSERT INTO keystroke_samples
                    (user_id, session_id, phase, enrollment, question_id,
                     events_json, meta_json, score, verdict, paste_flag, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        session_id_val,
                        phase_val,
                        1 if enrollment else 0,
                        question_id or "",
                        json.dumps(events),
                        json.dumps(meta or {}),
                        score_val,
                        verdict_label,
                        int(paste_flag),
                        ts,
                    ),
                )
            except Exception as e:
                logger.warning("Could not store raw sample: %s", e)

        ts = now_ts()

        # enrollment branch
        if enrollment:
            if vec is None:
                raise HTTPException(status_code=500, detail="feature extraction failed")
            blob = vec.tobytes() if hasattr(vec, "tobytes") else b""
            cur.execute(
                "INSERT INTO profiles(user_id, embedding, device_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, sqlite3.Binary(blob), device_info or "", ts, ts),
            )

            # NEW: also store this enrollment sample in keystroke_samples
            _store_raw_sample(
                session_id_val=None,
                phase_val=phase,
                verdict_label="enroll",
                score_val=None,
            )

            conn.commit()
            conn.close()
            return {"status": "enrolled", "phase": phase, "meta": meta}

                # verification branch
        cur.execute("SELECT embedding FROM profiles WHERE user_id = ?", (user_id,))
        rows = cur.fetchall()
        templates = []
        for r in rows:
            if r and r[0]:
                try:
                    templates.append(bytes_to_vector(r[0]))
                except Exception:
                    logger.exception("failed to convert embedding")

        verdict_res = decide_score_and_verdict(vec, templates, paste_flag)

        session_id = str(uuid.uuid4())
        notes = json.dumps({
            "phase": phase,
            "test_id": test_id,
            "model_version": MODEL_VERSION,
            "meta": meta,
        })

        # NEW: store raw sample + meta + verdict in keystroke_samples
        _store_raw_sample(
            session_id_val=session_id,
            phase_val=phase,
            verdict_label=verdict_res.get("verdict"),
            score_val=verdict_res.get("score"),
        )

        cur.execute(
            "INSERT INTO sessions(session_id, user_id, question_id, timestamp, score, verdict, paste_flag, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                user_id,
                question_id or "",
                ts,
                verdict_res.get("score"),
                verdict_res.get("verdict"),
                int(paste_flag),
                notes,
            ),
        )
        conn.commit()
        conn.close()

        return {
            "score": verdict_res.get("score"),
            "verdict": verdict_res.get("verdict"),
            "paste_flag": paste_flag,
            "meta": meta,
            "phase": phase,
            "session_id": session_id,
        }


    except HTTPException:
        raise
    except Exception as exc:
        tb = traceback.format_exc()
        with open("submit_events_error.log", "w", encoding="utf-8") as f:
            f.write(tb)
        raise HTTPException(status_code=500, detail={"error": str(exc), "traceback": tb.splitlines()[-30:]})

# ---------------- Compatibility endpoints (safe fallbacks) -----------------
# (unchanged — these power the demo UI if your full candidate routes are not present)
SERVER_DATA_DIR = Path(__file__).resolve().parent.parent / "server_data"
SERVER_DATA_DIR.mkdir(parents=True, exist_ok=True)
ENROLL_FILE = SERVER_DATA_DIR / "enrollments.json"
TEMPLATE_FILE = SERVER_DATA_DIR / "templates.json"
if not ENROLL_FILE.exists(): ENROLL_FILE.write_text(json.dumps({}), encoding='utf8')
if not TEMPLATE_FILE.exists(): TEMPLATE_FILE.write_text(json.dumps({}), encoding='utf8')

def load_server_json(p: Path):
    try:
        return json.loads(p.read_text(encoding='utf8'))
    except Exception:
        return {}

def save_server_json(p: Path, obj):
    p.write_text(json.dumps(obj, indent=2), encoding='utf8')

@app.post("/candidate/start")
def compat_candidate_start(body: Dict[str, Any]):
    token = body.get('token')
    sid = str(uuid.uuid4())
    return {"session_id": sid, "token": token, "questions": [{"question_id":1, "text":"Please write a short paragraph introducing yourself."}]}

@app.post("/candidate/enroll")
def compat_candidate_enroll(body: Dict[str, Any]):
    token = body.get('token')
    events = body.get('events', [])
    d = load_server_json(ENROLL_FILE)
    arr = d.get(token, [])
    arr.append(events)
    d[token] = arr
    save_server_json(ENROLL_FILE, d)
    return {"ok": True, "samples_count": len(arr)}

@app.post("/candidate/enroll_finish")
def compat_candidate_enroll_finish(body: Dict[str, Any]):
    token = body.get('token')
    d = load_server_json(ENROLL_FILE)
    samples = d.get(token, [])
    if not samples:
        raise HTTPException(status_code=400, detail='No enrollment samples for token')
    feats = [extract_features(s) for s in samples]
    def avg_field(name):
        vals = [f.get('meta', {}).get(name) for f in feats if isinstance(f, dict) and f.get('meta', {}).get(name) is not None]
        return (sum(vals)/len(vals)) if vals else None
    template = { 'mean_dwell': avg_field('mean_dwell'), 'mean_flight': avg_field('mean_flight'), '_num_samples': len(samples)}
    t = load_server_json(TEMPLATE_FILE)
    t[token] = template
    save_server_json(TEMPLATE_FILE, t)
    return {"ok": True, "template": template}

@app.post("/candidate/submit_answer")
def compat_candidate_submit(body: Dict[str, Any]):
    token = body.get('token')
    events = body.get('events', [])
    t = load_server_json(TEMPLATE_FILE)
    template = t.get(token)
    f = extract_features(events)
    meta = f.get("meta") if isinstance(f, dict) else {}
    mean_hold = meta.get("mean_dwell") or meta.get("mean_hold")
    mean_dd = meta.get("mean_flight") or meta.get("mean_dd")
    if not template or template.get("mean_dwell") is None or template.get("mean_flight") is None or mean_hold is None or mean_dd is None:
        return {"features": f, "score": None, "authenticity": "No template"}
    denom1 = template.get("mean_dwell") or 1.0
    denom2 = template.get("mean_flight") or 1.0
    d1 = abs(mean_hold - template.get("mean_dwell")) / denom1
    d2 = abs(mean_dd - template.get("mean_flight")) / denom2
    score = max(0.0, 1.0 - (0.6 * d1 + 0.4 * d2))
    sc = int(round(score * 100))
    verdict = "genuine" if sc >= 60 else "imposter"
    return {"features": f, "score": sc, "authenticity": verdict}
# ---------- NEW: store frontend sample into keystroke_samples ----------
from fastapi import Request
import time

@app.post("/api/submit_events")
async def api_submit_events(request: Request):
    """
    Store one keystroke sample into keystroke_samples.

    Payload comes from keystroke_demo.html:
    {
      user_id: str,
      question_id: "demo_1",
      events: [...],
      device_info: str,
      enrollment: bool,
      final_text: str,
      test_id: str,
      phase: "test" | "baseline",
      rhythm_sim: number or null,
      text_sim: number or null,
      param_sims: { feature: similarity, ... } or null
    }
    """
    body = await request.json()

    user_id     = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    question_id = body.get("question_id") or ""
    events      = body.get("events") or []
    device_info = body.get("device_info") or ""
    enrollment  = bool(body.get("enrollment", False))
    final_text  = body.get("final_text") or ""
    test_id     = body.get("test_id") or None
    phase       = (body.get("phase") or "test").lower()
    rhythm_sim  = body.get("rhythm_sim", None)
    text_sim    = body.get("text_sim", None)
    param_sims  = body.get("param_sims") or {}

    # score = frontend rhythm similarity (0–100)
    score = None
    if rhythm_sim is not None:
        try:
            score = float(rhythm_sim)
        except Exception:
            score = None

    # simple verdict using Option A logic (rhythm + text similarity)
    if score is None:
        verdict = "unknown"
    else:
        if text_sim is not None and text_sim >= 0.85 and score < 85:
            verdict = "possible_copy"
        elif score >= 85:
            verdict = "genuine"
        else:
            verdict = "imposter"

    paste_flag = any(e.get("type") == "paste" for e in events)

    meta = {
        "frontend_rhythm_sim": rhythm_sim,
        "frontend_text_sim": text_sim,
        "frontend_param_sims": param_sims,
        "final_text": final_text,
        "device_info": device_info,
        "paste_flag": paste_flag,
        "phase": phase,
        "test_id": test_id,
        "event_count": len(events),
    }

    conn = get_conn()
    cur = conn.cursor()
    ts = int(time.time())

    try:
        cur.execute(
            """
            INSERT INTO keystroke_samples
            (user_id, session_id, phase, enrollment, question_id,
             events_json, meta_json, score, verdict, paste_flag, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                test_id,                # we use test_id from frontend as session_id
                phase,
                1 if enrollment else 0,
                question_id,
                json.dumps(events),
                json.dumps(meta),
                score,
                verdict,
                int(paste_flag),
                ts,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "score": score,
        "verdict": verdict,
        "paste_flag": paste_flag,
        "saved": True,
    }
# ---------- END /api/submit_events ----------
# ---------- NEW: store frontend sample into keystroke_samples ----------
from fastapi import Request
import time
import json

@app.post("/api/submit_events")
async def api_submit_events(request: Request):
    """
    Store one keystroke sample into keystroke_samples.

    Works even if frontend only sends:
      user_id, question_id, events, final_text, device_info, phase, test_id
    Extra fields (rhythm_sim, text_sim, param_sims) are optional.
    """
    body = await request.json()

    user_id     = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    question_id = body.get("question_id") or ""
    events      = body.get("events") or []
    device_info = body.get("device_info") or ""
    enrollment  = bool(body.get("enrollment", False))
    final_text  = body.get("final_text") or ""
    test_id     = body.get("test_id") or None
    phase       = (body.get("phase") or "test").lower()

    # OPTIONAL fields from frontend
    rhythm_sim  = body.get("rhythm_sim", None)   # 0–100 from UI
    text_sim    = body.get("text_sim", None)     # 0–1 from UI
    param_sims  = body.get("param_sims") or {}   # per-parameter similarities

    # Try to use rhythm_sim as score
    score = None
    if rhythm_sim is not None:
        try:
            score = float(rhythm_sim)
        except Exception:
            score = None

    # Simple verdict logic if we have score
    if score is None:
        verdict = "unknown"
    else:
        if text_sim is not None and text_sim >= 0.85 and score < 85:
            verdict = "possible_copy"
        elif score >= 85:
            verdict = "genuine"
        else:
            verdict = "imposter"

    paste_flag = any(e.get("type") == "paste" for e in events)

    meta = {
        "frontend_rhythm_sim": rhythm_sim,
        "frontend_text_sim": text_sim,
        "frontend_param_sims": param_sims,
        "final_text": final_text,
        "device_info": device_info,
        "paste_flag": paste_flag,
        "phase": phase,
        "test_id": test_id,
        "event_count": len(events),
    }

    conn = get_conn()
    cur = conn.cursor()
    ts = int(time.time())

    try:
        cur.execute(
            """
            INSERT INTO keystroke_samples
            (user_id, session_id, phase, enrollment, question_id,
             events_json, meta_json, score, verdict, paste_flag, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                test_id,                # using test_id from UI as session_id
                phase,
                1 if enrollment else 0,
                question_id,
                json.dumps(events),
                json.dumps(meta),
                score,
                verdict,
                int(paste_flag),
                ts,
            ),
        )
        conn.commit()
        print("✔ api_submit_events: stored sample for", user_id, "score=", score, "verdict=", verdict)
    except Exception as e:
        print("✖ api_submit_events DB error:", e)
        raise HTTPException(status_code=500, detail=f"DB insert failed: {e}")
    finally:
        conn.close()

    return {
        "score": score,
        "verdict": verdict,
        "paste_flag": paste_flag,
        "saved": True,
    }
# ---------- END /api/submit_events ----------
# ---------- NEW: store frontend sample into keystroke_samples ----------
from fastapi import Request
import time
import json

@app.post("/api/submit_events")
async def api_submit_events(request: Request):
    """
    Store one keystroke sample into keystroke_samples.

    Works even if frontend only sends:
      user_id, question_id, events, final_text, device_info, phase, test_id
    Extra fields (rhythm_sim, text_sim, param_sims) are optional.
    """
    body = await request.json()

    user_id     = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    question_id = body.get("question_id") or ""
    events      = body.get("events") or []
    device_info = body.get("device_info") or ""
    enrollment  = bool(body.get("enrollment", False))
    final_text  = body.get("final_text") or ""
    test_id     = body.get("test_id") or None
    phase       = (body.get("phase") or "test").lower()

    # OPTIONAL fields from frontend
    rhythm_sim  = body.get("rhythm_sim", None)   # 0–100 from UI
    text_sim    = body.get("text_sim", None)     # 0–1 from UI
    param_sims  = body.get("param_sims") or {}   # per-parameter similarities

    # Try to use rhythm_sim as score
    score = None
    if rhythm_sim is not None:
        try:
            score = float(rhythm_sim)
        except Exception:
            score = None

    # Simple verdict logic if we have score
    if score is None:
        verdict = "unknown"
    else:
        if text_sim is not None and text_sim >= 0.85 and score < 85:
            verdict = "possible_copy"
        elif score >= 85:
            verdict = "genuine"
        else:
            verdict = "imposter"

    paste_flag = any(e.get("type") == "paste" for e in events)

    meta = {
        "frontend_rhythm_sim": rhythm_sim,
        "frontend_text_sim": text_sim,
        "frontend_param_sims": param_sims,
        "final_text": final_text,
        "device_info": device_info,
        "paste_flag": paste_flag,
        "phase": phase,
        "test_id": test_id,
        "event_count": len(events),
    }

    conn = get_conn()
    cur = conn.cursor()
    ts = int(time.time())

    try:
        cur.execute(
            """
            INSERT INTO keystroke_samples
            (user_id, session_id, phase, enrollment, question_id,
             events_json, meta_json, score, verdict, paste_flag, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                test_id,                # using test_id from UI as session_id
                phase,
                1 if enrollment else 0,
                question_id,
                json.dumps(events),
                json.dumps(meta),
                score,
                verdict,
                int(paste_flag),
                ts,
            ),
        )
        conn.commit()
        print("✔ api_submit_events: stored sample for", user_id, "score=", score, "verdict=", verdict)
    except Exception as e:
        print("✖ api_submit_events DB error:", e)
        raise HTTPException(status_code=500, detail=f"DB insert failed: {e}")
    finally:
        conn.close()

    return {
        "score": score,
        "verdict": verdict,
        "paste_flag": paste_flag,
        "saved": True,
    }
# ---------- END /api/submit_events ----------

# expose debug helper
app.state._backend_info = {
    "db": str(Path(__file__).resolve().parent / "keystroke.db"),
    "static": str(static_dir)
}
