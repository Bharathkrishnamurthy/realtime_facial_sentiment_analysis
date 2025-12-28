# app/realtime_routes.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import app.database as database
from app.feature_extractor import extract_features
from app.matcher import bytes_to_vector, decide_score_and_verdict
import numpy as np, logging, json

router = APIRouter(prefix="/api", tags=["api"])
logger = logging.getLogger("keystroke_realtime")

class LiveScoreReq(BaseModel):
    candidate_id: Optional[int] = None   # prefer candidate_id for local templates
    user_id: Optional[str] = None        # fallback to user_id -> profiles.user_id
    events: List[dict]

@router.post("/score_live")
def score_live(req: LiveScoreReq):
    """
    Compute a similarity score for a short rolling window of events.
    Accepts candidate_id or user_id to look up stored templates.
    Returns score (0..1 float), verdict (accepted/review/rejected/no_template), meta.
    """
    if not req.events:
        raise HTTPException(status_code=400, detail="events required")

    db = database.database.get_conn()
    try:
        # load template embeddings from profiles table
        templates = []
        if req.candidate_id:
            rows = db.execute("SELECT embedding, template FROM profiles WHERE user_id = ? OR id = ?",
                              (str(req.candidate_id), req.candidate_id)).fetchall()
        elif req.user_id:
            rows = db.execute("SELECT embedding, template FROM profiles WHERE user_id = ? LIMIT 10",
                              (req.user_id,)).fetchall()
        else:
            rows = []

        for r in rows:
            # prefer binary embedding column; fallback to JSON template_features
            try:
                emb = None
                if r and len(r) >= 1 and r[0] is not None:
                    emb = bytes_to_vector(r[0])
                elif r and len(r) >= 2 and r[1]:
                    # try reading template_features.json -> construct a tiny vector from mean_hold/mean_dd
                    try:
                        tpl_json = json.loads(r[1])
                        tf = tpl_json.get("template_features") or tpl_json.get("template") or tpl_json
                        if tf and tf.get("mean_hold") is not None:
                            # simple two-dim vector -> turn into float32 vector of length 64 to match model
                            v = np.zeros(64, dtype=np.float32)
                            v[0] = float(tf.get("mean_hold", 0.0))
                            v[2] = float(tf.get("mean_dd", 0.0))
                            # simple normalization
                            n = np.linalg.norm(v) or 1.0
                            v = v / n
                            emb = v
                    except Exception:
                        pass
                if emb is not None:
                    templates.append(emb)
            except Exception:
                logger.exception("template decode failed")

        feat_res = extract_features(req.events)
        vec = feat_res.get("feature_vector")
        paste_flag = feat_res.get("paste_flag", False)
        meta = feat_res.get("meta", {})

        # if templates empty -> no_template
        if not templates:
            return {"score": None, "verdict": "no_template", "meta": meta}

        # ensure numpy array for vec
        try:
            import numpy as np
            if not isinstance(vec, np.ndarray):
                # feature_extractor returns numpy vector; but be defensive
                vec = np.array(vec, dtype=np.float32)
        except Exception:
            pass

        verdict = decide_score_and_verdict(vec, templates, paste_flag)
        # return human-friendly numeric score 0..1
        score = float(verdict.get("score") or 0.0)
        vname = verdict.get("verdict")
        return {"score": score, "verdict": vname, "meta": meta}
    finally:
        try: db.close()
        except: pass

@router.get("/profile/{candidate_id}")
def get_profile(candidate_id: int):
    """Return stored profile template and embedding info for a candidate (if exists)."""
    db = database.database.get_conn()
    try:
        row = db.execute("SELECT id, user_id, template, created_at, updated_at FROM profiles WHERE user_id = ? OR id = ? LIMIT 1",
                         (str(candidate_id), candidate_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="profile not found")
        # row may be sqlite3.Row or tuple
        try:
            tpl_json = row["template"]
            pid = row["id"]
            uid = row["user_id"]
            created = row.get("created_at", None)
            updated = row.get("updated_at", None)
        except Exception:
            pid, uid, tpl_json, created, updated = row[0], row[1], row[2], row[3] if len(row) > 3 else None, row[4] if len(row) > 4 else None
        try:
            tpl = json.loads(tpl_json) if tpl_json else None
        except Exception:
            tpl = None
        return {"id": pid, "user_id": uid, "template": tpl, "created_at": created, "updated_at": updated}
    finally:
        try: db.close()
        except: pass

@router.post("/submit_events_legacy")
async def submit_events_legacy(request: Request):
    """
    Lightweight compatibility wrapper for older frontends that post generic events.
    Accepts JSON with: user_id (or candidate_id), events, final_text, enrollment flag.
    Behaves similarly to your previous /api/submit_events but simplified for demo.
    """
    body = await request.json()
    user_id = body.get("user_id") or body.get("candidate_id")
    events = body.get("events", [])
    enrollment = bool(body.get("enrollment", False))
    final_text = body.get("final_text", "")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    # reuse feature extractor/matcher logic
    db = database.database.get_conn()
    try:
        feat = extract_features(events)
        vec = feat.get("feature_vector")
        paste_flag = feat.get("paste_flag", False)
        # enroll vs verify simplified
        if enrollment:
            db.execute("INSERT INTO profiles (user_id, template, created_at, updated_at) VALUES (?, ?, datetime('now'), datetime('now'))",
                       (str(user_id), json.dumps({"template_features": feat.get("meta", {})})))
            db.commit()
            return {"status": "enrolled", "meta": feat.get("meta", {})}
        # verification: load templates
        rows = db.execute("SELECT embedding, template FROM profiles WHERE user_id = ?", (str(user_id),)).fetchall()
        templates = []
        for r in rows:
            if r[0]:
                try:
                    import numpy as np
                    templates.append(bytes_to_vector(r[0]))
                except Exception:
                    pass
            elif r[1]:
                try:
                    tplj = json.loads(r[1])
                    tf = tplj.get("template_features") or tplj
                    import numpy as np
                    v = np.zeros(64, dtype=np.float32)
                    v[0] = float(tf.get("mean_hold", 0.0))
                    v[2] = float(tf.get("mean_dd", 0.0))
                    n = np.linalg.norm(v) or 1.0
                    templates.append(v / n)
                except Exception:
                    pass
        res = decide_score_and_verdict(vec, templates, paste_flag)
        return {"score": float(res.get("score") or 0.0), "verdict": res.get("verdict"), "meta": feat.get("meta", {})}
    finally:
        try: db.close()
        except: pass
