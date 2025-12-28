# app/enroll_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json, logging
import app.database as database
from app.session_service import compute_template_from_samples, _now_str

logger = logging.getLogger("keystroke_enroll")
router = APIRouter(prefix="/candidate", tags=["candidate"])

class EnrollSampleReq(BaseModel):
    token: str = None
    session_id: str = None
    events: list

class EnrollFinishReq(BaseModel):
    token: str = None
    session_id: str = None
    finalize: bool = True

def _resolve_candidate_id(db, token=None, session_id=None):
    if token:
        row = db.execute("SELECT candidate_id FROM assignments WHERE token = ? LIMIT 1", (token,)).fetchone()
        if row:
            try:
                return row["candidate_id"]
            except Exception:
                return row[0]
    if session_id:
        row = db.execute("SELECT candidate_id FROM sessions WHERE session_id = ? LIMIT 1", (session_id,)).fetchone()
        if row:
            try:
                return row["candidate_id"]
            except Exception:
                return row[0]
    return None

@router.post("/enroll")
def enroll_sample(req: EnrollSampleReq):
    db = database.database.get_conn()
    candidate_id = _resolve_candidate_id(db, token=req.token, session_id=req.session_id)
    if not candidate_id:
        raise HTTPException(status_code=404, detail="Candidate not found for token/session")

    # store samples in profiles.template JSON {samples: [...]}
    try:
        prof = db.execute("SELECT id, template FROM profiles WHERE user_id = ? LIMIT 1", (str(candidate_id),)).fetchone()
        if not prof:
            template_obj = {"samples": [req.events]}
            db.execute("INSERT INTO profiles (user_id, created_at, template) VALUES (?, ?, ?)",
                       (str(candidate_id), _now_str(), json.dumps(template_obj)))
            db.commit()
            samples_count = 1
        else:
            # prof may be Row or tuple
            prof_id = prof["id"] if hasattr(prof, "keys") and "id" in prof.keys() else prof[0]
            cur_template = json.loads(prof["template"]) if prof["template"] else {"samples": []}
            cur_template.setdefault("samples", []).append(req.events)
            db.execute("UPDATE profiles SET template = ?, updated_at = ? WHERE id = ?",
                       (json.dumps(cur_template), _now_str(), prof_id))
            db.commit()
            samples_count = len(cur_template["samples"])
    except Exception as e:
        logger.exception("failed to save enroll sample")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try: db.close()
        except: pass

    return {"status": "ok", "samples_count": samples_count}

@router.post("/enroll_finish")
def enroll_finish(req: EnrollFinishReq):
    db = database.database.get_conn()
    candidate_id = _resolve_candidate_id(db, token=req.token, session_id=req.session_id)
    if not candidate_id:
        raise HTTPException(status_code=404, detail="Candidate not found")
    prof = db.execute("SELECT id, template FROM profiles WHERE user_id = ? LIMIT 1", (str(candidate_id),)).fetchone()
    if not prof:
        raise HTTPException(status_code=404, detail="No enrollment samples for candidate")

    prof_id = prof["id"] if hasattr(prof, "keys") and "id" in prof.keys() else prof[0]
    template_json = json.loads(prof["template"]) if prof["template"] else {"samples": []}
    samples = template_json.get("samples", [])
    if not samples:
        raise HTTPException(status_code=400, detail="No samples collected")

    tpl = compute_template_from_samples(samples)
    template_json["template_features"] = tpl
    try:
        db.execute("UPDATE profiles SET template = ?, updated_at = ? WHERE id = ?",
                   (json.dumps(template_json), _now_str(), prof_id))
        db.commit()
    except Exception as e:
        logger.exception("failed to persist computed template")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try: db.close()
        except: pass

    return {"status": "ok", "template": tpl}
