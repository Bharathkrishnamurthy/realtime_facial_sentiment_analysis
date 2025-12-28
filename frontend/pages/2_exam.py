import sys
import time
import uuid
from pathlib import Path

import streamlit as st
from modules.Keystroke_dynamics.backend.service import verify_keystroke_session

# ---------------- PATH FIX (VERY IMPORTANT) ----------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.exam.mcq_engine import load_questions
from src.session.session_manager import get_session, stop_monitoring

# ---------------- CONFIG ----------------
QUESTION_TIME = 10  # seconds per question
# ----------------------------------------

st.set_page_config(page_title="Exam", layout="wide")

# ================= SESSION VALIDATION =================
if "session_id" not in st.session_state:
    st.error("Session expired. Please login again.")
    st.stop()

session = get_session(st.session_state["session_id"])
questions = load_questions()

# ================= CREATE EXAM SESSION ID (KEYSTEP) =================
if "exam_session_id" not in st.session_state:
    st.session_state.exam_session_id = str(uuid.uuid4())

# (Optional – helpful for debugging)
st.sidebar.markdown("### Exam Session ID")
st.sidebar.code(st.session_state.exam_session_id)

# ================= INITIALIZE EXAM STATE =================
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
    st.session_state.q_start_time = time.time()
    st.session_state.auto_advanced = False

# ================= EXAM COMPLETED =================
if st.session_state.q_index >= len(questions):
    st.success("✅ All questions completed")

    if st.button("Submit Exam"):
        # 1️⃣ Stop webcam / tab / monitoring
        stop_monitoring(st.session_state["session_id"])

        # 2️⃣ VERIFY KEYSTROKE DYNAMICS (STEP 7 CORE)
        with st.spinner("🔍 Verifying keystroke dynamics..."):
            keystroke_result = verify_keystroke_session(
                st.session_state.exam_session_id
            )

        # 3️⃣ Store result for report page
        st.session_state.keystroke_result = keystroke_result

        # 4️⃣ Go to report
        st.switch_page("pages/3_Report.py")

    st.stop()

# ================= CURRENT QUESTION =================
q_index = st.session_state.q_index
q = questions[q_index]

st.sidebar.info(f"Question {q_index + 1} / {len(questions)}")

st.title("📝 Online Exam")
st.subheader(q["question"])

selected = st.radio(
    "Choose your answer:",
    q["options"],
    key=f"q_{q_index}"
)

# ================= TIMER =================
elapsed = int(time.time() - st.session_state.q_start_time)
remaining = max(0, QUESTION_TIME - elapsed)

st.warning(f"⏱️ Time left: {remaining} seconds")

# ================= AUTO NEXT (TIME UP) =================
if remaining == 0 and not st.session_state.auto_advanced:
    session["answers"].append({
        "question_id": q["id"],
        "answer": selected
    })

    st.session_state.q_index += 1
    st.session_state.q_start_time = time.time()
    st.session_state.auto_advanced = True
    st.rerun()

# ================= MANUAL NEXT =================
if st.button("Next"):
    session["answers"].append({
        "question_id": q["id"],
        "answer": selected
    })

    st.session_state.q_index += 1
    st.session_state.q_start_time = time.time()
    st.session_state.auto_advanced = False
    st.rerun()

# ================= RESET AUTO FLAG =================
if elapsed == 0:
    st.session_state.auto_advanced = False
