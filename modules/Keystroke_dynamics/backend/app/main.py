from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any
from uuid import uuid4
from pathlib import Path
import json, statistics, time
from .database import init_db, get_conn
from .user_routes import router as user_router

def now_ts():
    return int(time.time())

SAMPLES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS keystroke_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  token TEXT,
  session_id TEXT,
  phase TEXT,
  enrollment INTEGER,
  question_id TEXT,
  final_text TEXT,
  events_json TEXT,
  meta_json TEXT,
  live_rhythm_sim REAL,
  live_text_sim REAL,
  created_at INTEGER
);
"""

TEMPLATES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS keystroke_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  template_json TEXT,
  created_at INTEGER
);
"""

def ensure_keystroke_tables():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(SAMPLES_TABLE_SQL)
    cur.execute(TEMPLATES_TABLE_SQL)
    conn.commit()
    conn.close()

DATA_DIR = Path(__file__).resolve().parent.parent / "server_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
ENROLLMENTS_FILE = DATA_DIR / "enrollments.json"
TEMPLATES_FILE = DATA_DIR / "templates.json"
def load_json(path):
    if not path.exists(): return {}
    with path.open("r", encoding="utf8") as f: return json.load(f)
def save_json(path, obj):
    with path.open("w", encoding="utf8") as f: json.dump(obj, f, indent=2)
if not ENROLLMENTS_FILE.exists(): save_json(ENROLLMENTS_FILE, {})
if not TEMPLATES_FILE.exists(): save_json(TEMPLATES_FILE, {})

def extract_features_from_events(events: List[Dict[str,Any]]):
    events = sorted(events, key=lambda e: e.get("ts",0))
    last_down = {}
    holds = []
    for e in events:
        t = e.get("ts")
        if e.get("type","").lower().startswith("keydown"):
            last_down[e.get("key")] = t
        elif e.get("type","").lower().startswith("keyup"):
            k = e.get("key")
            if k in last_down and last_down[k] is not None and t is not None:
                holds.append(t - last_down[k]); del last_down[k]
    prev_down = None; dd = []
    for e in events:
        if e.get("type","").lower().startswith("keydown"):
            if prev_down is not None and e.get("ts") is not None: dd.append(e.get("ts") - prev_down)
            prev_down = e.get("ts")
    mean_hold = statistics.mean(holds) if len(holds) else None
    mean_dd = statistics.mean(dd) if len(dd) else None
    return {"mean_hold": mean_hold, "mean_dd": mean_dd, "num_events": len(events)}

def compute_template_from_samples(samples: List[List[Dict]]):
    if not samples: return None
    feats = [extract_features_from_events(s) for s in samples]
    def avg(field):
        vals = [f[field] for f in feats if f.get(field) is not None]
        return statistics.mean(vals) if vals else None
    return {"mean_hold": avg("mean_hold"), "mean_dd": avg("mean_dd"), "_num_samples": len(samples)}

def similarity_score(features, template):
    if not template or template.get("mean_hold") is None or template.get("mean_dd") is None:
        return None
    d1 = abs((features.get("mean_hold") or 0) - template.get("mean_hold")) / (template.get("mean_hold") or 1)
    d2 = abs((features.get("mean_dd") or 0) - template.get("mean_dd")) / (template.get("mean_dd") or 1)
    score = max(0.0, 1.0 - (0.6 * d1 + 0.4 * d2))
    return int(round(score * 100))

app = FastAPI(title="Keystroke Demo Minimal API")

@app.on_event("startup")
async def startup_event():
    init_db()
    ensure_keystroke_tables()

# --- quick create_user endpoint (place this AFTER app = FastAPI()) ---
@app.get("/api/users")
def list_users():
    conn = get_conn()
    rows = conn.execute("SELECT user_id, created_at FROM users ORDER BY created_at DESC LIMIT 100").fetchall()
    conn.close()
    return [{"user_id": r[0], "created_at": r[1]} for r in rows]


# --- debug create_user handler (paste AFTER app = FastAPI()) ---
from fastapi import Request, Response
import uuid
import time
import json
from .database import get_conn, logger  # logger writes to keystroke_db.log

@app.post("/api/create_user")
async def create_user_debug(req: Request):
    """
    Debugging wrapper for create_user: logs exception traceback to keystroke_db.log
    and returns the exception details in the HTTP response body (JSON).
    """
    try:
        # minimal create (compatible with current DB)
        user_id = str(uuid.uuid4())
        created_at = int(time.time())

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
          CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at INTEGER
          )
        """)
        cur.execute("INSERT INTO users (user_id, created_at) VALUES (?, ?)", (user_id, created_at))
        conn.commit()
        conn.close()

        return {"user_id": user_id}
    except Exception as exc:
        # log full traceback to your DB log file
        try:
            logger.exception("create_user_debug failed")
        except Exception:
            # fallback: print if logger not available
            import traceback as _tb
            _tb.print_exc()
        # return error details in the response body (safe for debugging)
        body = {"detail": "Internal Server Error", "error": str(exc)}
        return Response(content=json.dumps(body), status_code=500, media_type="application/json")
# --- end debug handler ---
@app.post("/api/save_template")
async def save_template(req: Request):
    """
    Save one template for a user. Called by the demo UI 'Save current as template'.
    Template is stored as JSON in keystroke_templates.
    """
    body = await req.json()
    user_id = body.get("user_id")
    template = body.get("template")
    if not user_id or not template:
        raise HTTPException(status_code=400, detail="user_id and template required")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO keystroke_templates (user_id, template_json, created_at) VALUES (?, ?, ?)",
        (user_id, json.dumps(template), now_ts()),
    )
    conn.commit()
    conn.close()
    return {"ok": True}
    

@app.get("/api/templates")
def list_templates(user_id: str):
    """
    Return all templates for a given user as a list of JSON objects.
    Used by the demo UI to populate the Templates dropdown.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT template_json FROM keystroke_templates WHERE user_id = ? ORDER BY id ASC",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    templates = []
    for (tpl_json,) in rows:
        try:
            templates.append(json.loads(tpl_json))
        except Exception:
            continue
    return templates


app.include_router(user_router)
# add near where you include other routers (after app.include_router(user_router))
from app.candidate_routes import router as candidate_router
app.include_router(candidate_router)

class StartIn(BaseModel):
    token: str
class EnrollIn(BaseModel):
    token: str
    events: List[Dict[str,Any]]
class EnrollFinishIn(BaseModel):
    token: str
class SubmitIn(BaseModel):
    session_id: str = None
    question_id: int = None
    final_text: str = None
    token: str = None
    events: List[Dict[str,Any]]


@app.post("/candidate/start")
def candidate_start(body: StartIn):
    sid = str(uuid4())
    return {"session_id": sid, "token": body.token, "questions": [{"question_id":1,"text":"Please introduce yourself."}]}

@app.post("/candidate/enroll")
def candidate_enroll(body: EnrollIn):
    enrollments = load_json(ENROLLMENTS_FILE)
    arr = enrollments.get(body.token, [])
    arr.append(body.events)
    enrollments[body.token] = arr
    save_json(ENROLLMENTS_FILE, enrollments)
    return {"ok": True, "samples_count": len(arr)}

@app.post("/candidate/enroll_finish")
def candidate_enroll_finish(body: EnrollFinishIn):
    enrollments = load_json(ENROLLMENTS_FILE)
    token_samples = enrollments.get(body.token, [])
    if not token_samples:
        raise HTTPException(status_code=400, detail="No enrollment samples for token")
    template = compute_template_from_samples(token_samples)
    templates = load_json(TEMPLATES_FILE)
    templates[body.token] = template
    save_json(TEMPLATES_FILE, templates)
    return {"ok": True, "template": template}

@app.post("/candidate/submit_answer")
def candidate_submit_answer(body: SubmitIn):
    templates = load_json(TEMPLATES_FILE)
    template = templates.get(body.token)
    features = extract_features_from_events(body.events or [])
    score = similarity_score(features, template)
    verdict = "No template" if score is None else ("genuine" if score >= 60 else "imposter")
    return {"features": features, "score": score, "authenticity": verdict}
# ---------- NEW: store frontend sample into keystroke_samples ----------
from fastapi import Request
import time, json

@app.post("/api/submit_events")
async def api_submit_events(request: Request):
    """
    Store one keystroke sample into keystroke_samples.

    Payload from keystroke_demo.html:
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

    # optional similarities sent from frontend
    rhythm_sim  = body.get("rhythm_sim", None)   # 0–100
    text_sim    = body.get("text_sim", None)     # 0–1
    param_sims  = body.get("param_sims") or {}   # 9 parameter similarities

    # score = rhythm similarity
    score = None
    if rhythm_sim is not None:
        try:
            score = float(rhythm_sim)
        except Exception:
            score = None

    # simple verdict using rhythm + text similarity (your Option A logic)
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
        "frontend_param_sims": param_sims,  # 9-parameter similarity map
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
                test_id,                # use test_id as session_id
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

@app.get("/ping")
def ping():
    return {"status":"ok", "time": int(time.time())}


from fastapi.responses import FileResponse

_demo_abs_path = r"C:\Users\Dell\Desktop\Keystroke_dynamics\backend\app\static\keystroke_demo.html"

@app.get("/keystroke_demo.html")
def _serve_demo_root():
    import os
    if os.path.exists(_demo_abs_path):
        return FileResponse(_demo_abs_path)
    raise HTTPException(status_code=404, detail="Demo HTML not found at expected path")

@app.get("/static/keystroke_demo.html")
def _serve_demo_static_path():
    import os
    if os.path.exists(_demo_abs_path):
        return FileResponse(_demo_abs_path)
    raise HTTPException(status_code=404, detail="Demo HTML not found at expected path")

@app.post("/api/submit_events")
async def submit_events(req: Request):
    """
    Store one keystroke sample in SQLite.
    Called by the demo UI when you click 'Done (compute & compare)'.
    We store:
      - user_id, token, session_id/test_id, phase, enrollment
      - question_id, final_text
      - full events_json
      - meta_json including basic backend features and frontend live scores
    """
    body = await req.json()

    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")

    events = body.get("events") or []
    final_text = body.get("final_text") or ""
    question_id = body.get("question_id") or ""
    token = body.get("token") or ""
    phase = (body.get("phase") or "test").lower()
    enrollment = bool(body.get("enrollment") or False)
    test_id = body.get("test_id") or str(uuid4())

    # frontend-provided live similarity
    rhythm_sim = body.get("rhythm_sim")     # 0..100
    text_sim = body.get("text_sim")         # 0..1
    param_sims = body.get("param_sims")     # dict or None

    # basic backend features (3-parameter model)
    feats_basic = extract_features_from_events(events)

    # meta combines backend features + frontend analytics + device info
    meta = {
        "feats_basic": feats_basic,
        "frontend_rhythm_sim": rhythm_sim,
        "frontend_text_sim": text_sim,
        "frontend_param_sims": param_sims,
        "device_info": body.get("device_info"),
        "token": token,
    }

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO keystroke_samples
        (user_id, token, session_id, phase, enrollment, question_id,
         final_text, events_json, meta_json, live_rhythm_sim, live_text_sim, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            token,
            test_id,
            phase,
            1 if enrollment else 0,
            str(question_id),
            final_text,
            json.dumps(events),
            json.dumps(meta),
            rhythm_sim,
            text_sim,
            now_ts(),
        ),
    )
    conn.commit()
    conn.close()

    return {
        "status": "stored",
        "user_id": user_id,
        "question_id": question_id,
        "rhythm_sim": rhythm_sim,
        "text_sim": text_sim,
        "basic_features": feats_basic,
    }
