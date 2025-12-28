# app/session_service.py
import uuid, json, logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger("keystroke_session")

def _now_str():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def extract_features(events: List[Dict[str,Any]]):
    """Return simple aggregate features used by compute_template_from_samples and small metadata."""
    if not events:
        return {"mean_hold": None, "mean_dd": None, "num_events": 0}
    holds = []
    last_down = {}
    for e in events:
        t = e.get("ts")
        typ = e.get("type")
        key = e.get("key")
        if typ == "keydown":
            last_down[key] = t
        elif typ == "keyup" and key in last_down:
            holds.append(t - last_down[key])
            del last_down[key]
    dd = []
    prev_down = None
    for e in events:
        if e.get("type") == "keydown":
            if prev_down is not None:
                dd.append(e["ts"] - prev_down)
            prev_down = e["ts"]
    def mean(arr):
        return sum(arr)/len(arr) if arr else None
    return {"mean_hold": mean(holds), "mean_dd": mean(dd), "num_events": len(events)}

def compute_template_from_samples(samples: List[List[Dict[str,Any]]]):
    feats = [extract_features(s) for s in samples if s]
    if not feats:
        return None
    hold_vals = [f["mean_hold"] for f in feats if f["mean_hold"] is not None]
    dd_vals = [f["mean_dd"] for f in feats if f["mean_dd"] is not None]
    mean_hold = sum(hold_vals)/len(hold_vals) if hold_vals else None
    mean_dd = sum(dd_vals)/len(dd_vals) if dd_vals else None
    return {"mean_hold": mean_hold, "mean_dd": mean_dd, "n_samples": len(feats)}

# persistence helpers used by candidate_routes
def save_answer_and_biometrics(db, session_id: str, question_id: int, final_text: str, events: List[Dict[str,Any]]):
    ts = _now_str()
    # Save answer (try multiple common column names)
    try:
        db.execute("INSERT INTO answers (session_id, question_id, final_text, created_at) VALUES (?, ?, ?, ?)",
                   (session_id, question_id, final_text or "", ts))
        db.commit()
    except Exception:
        try:
            db.execute("INSERT INTO answers (session_id, question_id, answer_text, created_at) VALUES (?, ?, ?, ?)",
                       (session_id, question_id, final_text or "", ts))
            db.commit()
        except Exception as ex:
            logger.exception("failed to insert answer")
            raise ex

    # Save minimal feature log
    try:
        meta = {"events_count": len(events) if events else 0}
        db.execute("INSERT INTO feature_logs (session_id, question_id, meta, created_at) VALUES (?, ?, ?, ?)",
                   (session_id, question_id, json.dumps(meta), ts))
        db.commit()
    except Exception:
        # ignore if table missing or mismatched
        logger.debug("feature_logs insert skipped or failed", exc_info=True)

    # Optionally write raw keystroke_events rows (if table exists)
    try:
        for e in events or []:
            db.execute("INSERT INTO keystroke_events (session_id, event_json, created_at) VALUES (?, ?, ?)",
                       (session_id, json.dumps(e), ts))
        db.commit()
    except Exception:
        logger.debug("keystroke_events insert skipped or failed", exc_info=True)

    return True

def create_session_for_token(db, token: str):
    cur = db.execute("SELECT id, candidate_id, test_id FROM assignments WHERE token = ? LIMIT 1", (token,))
    row = cur.fetchone()
    if not row:
        return None, None
    try:
        assignment_id = row["id"]
        candidate_id = row["candidate_id"]
        test_id = row["test_id"]
    except Exception:
        assignment_id, candidate_id, test_id = row[0], row[1], row[2]
    session_id = str(uuid.uuid4())
    ts = _now_str()

    # try several insert variants
    inserted = False
    last_exc = None
    try:
        db.execute("INSERT INTO sessions (session_id, test_id, candidate_id, status, started_at, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                   (session_id, test_id, candidate_id, "active", ts, ts))
        db.commit()
        inserted = True
    except Exception as e:
        last_exc = e

    if not inserted:
        try:
            db.execute("INSERT INTO sessions (session_id, test_id, candidate_id, status, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (session_id, test_id, candidate_id, "active", int(datetime.utcnow().timestamp())))
            db.commit()
            inserted = True
        except Exception as e:
            last_exc = e

    if not inserted:
        raise RuntimeError(f"Failed to insert session row: {last_exc!r}")

    # ensure status/started_at saved
    try:
        db.execute("UPDATE sessions SET status = ?, started_at = ? WHERE session_id = ?", ("active", ts, session_id))
        db.commit()
    except Exception:
        pass

    return session_id, test_id

def get_questions_for_test(db, test_id: int):
    try:
        qrows = db.execute("""
            SELECT q.id AS question_id, q.text AS text, tq.seq AS seq
            FROM test_questions tq
            JOIN questions q ON q.id = tq.question_id
            WHERE tq.test_id = ?
            ORDER BY COALESCE(tq.seq, 0) ASC
        """, (test_id,)).fetchall()
    except Exception:
        qrows = db.execute("""
            SELECT q.id AS question_id, q.text AS text
            FROM test_questions tq
            JOIN questions q ON q.id = tq.question_id
            WHERE tq.test_id = ?
        """, (test_id,)).fetchall()

    out = []
    for r in qrows:
        try:
            qid = r["question_id"]
            text = r["text"]
            seq = r.get("seq", None) if hasattr(r, "get") else (r["seq"] if "seq" in r.keys() else None)
        except Exception:
            qid = r[0]; text = r[1]; seq = r[2] if len(r) > 2 else None
        out.append({"question_id": qid, "text": text, "seq": seq})
    return out

def finish_session(db, session_id: str):
    # compute score = answers / total questions (robust)
    s = db.execute("SELECT * FROM sessions WHERE session_id = ? LIMIT 1", (session_id,)).fetchone()
    if not s:
        raise ValueError("session not found")
    # robust test_id read
    try:
        test_id = s["test_id"] if "test_id" in s.keys() else s[4] if len(s) > 4 else None
    except Exception:
        test_id = None

    if not test_id:
        # try assignments
        try:
            a = db.execute("SELECT test_id FROM assignments WHERE id = ? LIMIT 1", (s.get("assignment_id") if hasattr(s, "get") else None,)).fetchone()
            if a:
                test_id = a["test_id"] if "test_id" in a.keys() else a[0]
        except Exception:
            pass

    # count answers
    try:
        answers_count = db.execute("SELECT COUNT(*) as c FROM answers WHERE session_id = ?", (session_id,)).fetchone()
        answers_count = answers_count["c"] if "c" in answers_count.keys() else answers_count[0]
    except Exception:
        answers_count = 0

    total_questions = None
    if test_id:
        try:
            tq = db.execute("SELECT COUNT(*) as c FROM test_questions WHERE test_id = ?", (test_id,)).fetchone()
            total_questions = tq["c"] if "c" in tq.keys() else tq[0]
        except Exception:
            total_questions = None

    score = 0.0
    if total_questions and total_questions > 0:
        score = float(answers_count) / float(total_questions)
    else:
        score = 1.0 if answers_count > 0 else 0.0

    authenticity = "authentic" if score >= 0.6 else ("suspicious" if score > 0 else "no_answers")
    now = _now_str()
    # update sessions row safely
    try:
        cols = [c[0] for c in db.execute("PRAGMA table_info(sessions)").fetchall()]
        if "finished_at" in cols:
            db.execute("UPDATE sessions SET status = ?, finished_at = ?, updated_at = ? WHERE session_id = ?",
                       ("finished", now, now, session_id))
        elif "status" in cols:
            db.execute("UPDATE sessions SET status = ?, updated_at = ? WHERE session_id = ?",
                       ("finished", now, session_id))
        elif "score" in cols and "verdict" in cols:
            db.execute("UPDATE sessions SET score = ?, verdict = ? WHERE session_id = ?", (score, authenticity, session_id))
        db.commit()
    except Exception:
        logger.debug("session update after finish may have failed", exc_info=True)

    return score, authenticity
