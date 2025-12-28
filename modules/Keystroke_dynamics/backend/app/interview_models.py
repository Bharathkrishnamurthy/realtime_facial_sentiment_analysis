# app/interview_models.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Literal

# ---------- HR: Questions & Tests ----------

class QuestionCreate(BaseModel):
    text: str
    qtype: Literal["mcq", "theory", "code"]
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None

class TestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    question_ids: List[int]

# ---------- HR: Candidates & assignment ----------

class CandidateCreate(BaseModel):
    # This links to keystroke.users.user_id
    user_id: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class AssignTestRequest(BaseModel):
    candidate_id: int
    test_id: int
