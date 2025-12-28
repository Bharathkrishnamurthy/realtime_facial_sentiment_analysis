import uuid
import time

SESSIONS = {}

def create_session(user_data):
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "user": user_data,
        "start_time": time.time(),
        "monitoring": True,
        "answers": [],
        "emotion_log": [],
        "malpractice": 0
    }
    return session_id

def get_session(session_id):
    return SESSIONS.get(session_id)

def stop_monitoring(session_id):
    if session_id in SESSIONS:
        SESSIONS[session_id]["monitoring"] = False
