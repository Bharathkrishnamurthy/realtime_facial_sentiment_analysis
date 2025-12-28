# app/interview_routes.py
from fastapi import APIRouter, HTTPException
from typing import List
import json, secrets, logging
import app.database as database
from .interview_models import QuestionCreate, TestCreate, CandidateCreate, AssignTestRequest
from app.database import get_conn, now_ts

logger = logging.getLogger("keystroke_interview")
router = APIRouter(prefix="/hr", tags=["hr"])

# create question
@router.post("/questions")
def create_question(q: QuestionCreate):
    if q.qtype == "mcq" and not q.options:
        raise HTTPException(status_code=400, detail="MCQ questions must have options")
    options_json = json.dumps(q.options) if q.options is not None else None
    db = database.get_conn()
    cur = db.cursor()
    try:
        cur.execute(
            "INSERT INTO questions(text, description, created_at) VALUES (?, ?, ?)",
            (q.text, None, now_ts())
        )
        qid = cur.lastrowid
        # If MCQ/advanced fields are needed, you can extend schema
        db.commit()
        return {"id": qid, "message": "question_created"}
    finally:
        try: db.close()
        except: pass

@router.get("/questions")
def list_questions():
    db = database.get_conn()
    cur = db.cursor()
    try:
        cur.execute("SELECT id, text, description, created_at FROM questions ORDER BY id")
        rows = cur.fetchall()
        out = [{"id": r[0], "text": r[1], "description": r[2], "created_at": r[3]} for r in rows]
        return out
    finally:
        try: db.close()
        except: pass

@router.post("/tests")
def create_test(t: TestCreate):
    if not t.question_ids:
        raise HTTPException(status_code=400, detail="question_ids cannot be empty")
    db = database.get_conn()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO tests(name, description, time_limit_minutes, created_at) VALUES (?, ?, ?, ?)",
                    (t.name, t.description or "", t.time_limit_minutes or 0, now_ts()))
        test_id = cur.lastrowid
        for idx, qid in enumerate(t.question_ids):
            cur.execute("INSERT INTO test_questions(test_id, question_id, seq) VALUES (?, ?, ?)",
                        (test_id, qid, idx))
        db.commit()
        return {"id": test_id, "message": "test_created", "question_ids": t.question_ids}
    finally:
        try: db.close()
        except: pass

@router.get("/tests")
def list_tests():
    db = database.get_conn()
    try:
        cur = db.cursor()
        cur.execute("SELECT id, name, description, time_limit_minutes, created_at FROM tests ORDER BY id")
        tests_rows = cur.fetchall()
        out = []
        for t in tests_rows:
            cur.execute("SELECT question_id, seq FROM test_questions WHERE test_id = ? ORDER BY seq", (t[0],))
            qrows = cur.fetchall()
            questions = [{"question_id": qr[0], "seq": qr[1]} for qr in qrows]
            out.append({"id": t[0], "name": t[1], "description": t[2], "time_limit_minutes": t[3], "created_at": t[4], "questions": questions})
        return out
    finally:
        try: db.close()
        except: pass

@router.post("/candidates")
def create_candidate(c: CandidateCreate):
    db = database.get_conn()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO candidates(user_id, name, email, created_at) VALUES (?, ?, ?, ?)",
                    (c.user_id, c.name or "", c.email or "", now_ts()))
        cid = cur.lastrowid
        db.commit()
        return {"id": cid, "message": "candidate_created"}
    finally:
        try: db.close()
        except: pass

@router.get("/candidates")
def list_candidates():
    db = database.get_conn()
    try:
        cur = db.cursor()
        cur.execute("SELECT id, user_id, name, email, created_at FROM candidates ORDER BY id")
        rows = cur.fetchall()
        out = [{"id": r[0], "user_id": r[1], "name": r[2], "email": r[3], "created_at": r[4]} for r in rows]
        return out
    finally:
        try: db.close()
        except: pass

@router.post("/assign_test")
def assign_test(req: AssignTestRequest):
    db = database.get_conn()
    cur = db.cursor()
    # ensure candidate exists
    cur.execute("SELECT id FROM candidates WHERE id = ? LIMIT 1", (req.candidate_id,))
    if not cur.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="candidate not found")
    # ensure test exists
    cur.execute("SELECT id FROM tests WHERE id = ? LIMIT 1", (req.test_id,))
    if not cur.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="test not found")
    token = secrets.token_urlsafe(16)
    cur.execute("INSERT INTO assignments(candidate_id, test_id, token, created_at) VALUES (?, ?, ?, ?)",
                (req.candidate_id, req.test_id, token, now_ts()))
    ct_id = cur.lastrowid
    db.commit()
    db.close()
    return {"candidate_test_id": ct_id, "token": token, "message": "test_assigned"}

@router.get("/candidate_tests")
def list_candidate_tests():
    db = database.get_conn()
    try:
        cur = db.cursor()
        cur.execute("""
            SELECT ct.id, ct.candidate_id, c.name, c.email, ct.test_id, t.name, ct.status, ct.token, ct.created_at
            FROM assignments ct
            JOIN candidates c ON c.id = ct.candidate_id
            JOIN tests t ON t.id = ct.test_id
            ORDER BY ct.id
        """)
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({"id": r[0], "candidate_id": r[1], "candidate_name": r[2], "candidate_email": r[3],
                        "test_id": r[4], "test_name": r[5], "status": r[6], "token": r[7], "created_at": r[8]})
        return out
    finally:
        try: db.close()
        except: pass
