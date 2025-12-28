# backend/app/candidate_schemas.py
from typing import List, Optional
from pydantic import BaseModel

class StartTestRequest(BaseModel):
    token: str

class QuestionOut(BaseModel):
    question_id: str
    text: str
    meta: Optional[dict] = None

class StartTestResponse(BaseModel):
    session_id: str
    test_id: int
    time_limit_secs: int
    questions: List[QuestionOut]

class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    final_text: str
    events: List[dict]

class SubmitAnswerResponse(BaseModel):
    status: str
    note: Optional[str] = None

class FinishTestRequest(BaseModel):
    session_id: str

class FinishTestResponse(BaseModel):
    status: str
    score: Optional[float] = None
    authenticity: Optional[float] = None
