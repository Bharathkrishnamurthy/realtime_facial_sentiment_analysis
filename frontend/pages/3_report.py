import sys
from pathlib import Path
import streamlit as st

# ---------------- PATH FIX ----------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.session.session_manager import get_session

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Exam Report", layout="wide")

st.title("📊 Exam Report")

# ---------------- SESSION VALIDATION ----------------
if "session_id" not in st.session_state:
    st.error("Session expired. Please login again.")
    st.stop()

session = get_session(st.session_state["session_id"])

# ================= BASIC DETAILS =================
st.subheader("👤 Candidate Info")
st.json(session.get("user", {}))

st.subheader("📝 Exam Summary")
st.write("Total Questions:", len(session.get("answers", [])))
st.write("Malpractice Count:", session.get("malpractice", 0))

# ================= EMOTION LOGS =================
st.subheader("😐 Emotion Logs (Sample)")
emotion_logs = session.get("emotion_log", [])

if emotion_logs:
    st.json(emotion_logs[:5])
else:
    st.info("No emotion logs available.")

# ================= STEP 8: PROCTORING SCORE =================
st.divider()
st.header("🔍 Proctoring Analysis")

# -------- Emotion Score --------
# Assume emotion_score stored as percentage (0–100)
raw_emotion_score = st.session_state.get("emotion_score", 70)
emotion_score = raw_emotion_score / 100
emotion_score = min(max(emotion_score, 0), 1)

# -------- Keystroke Score --------
keystroke_result = st.session_state.get("keystroke_result", {})
keystroke_score = keystroke_result.get("score", 0.5)

# -------- Tab Switch Discipline --------
tab_switch_count = st.session_state.get("tab_switch_count", session.get("malpractice", 0))

if tab_switch_count == 0:
    tab_score = 1.0
elif tab_switch_count <= 2:
    tab_score = 0.7
elif tab_switch_count <= 5:
    tab_score = 0.4
else:
    tab_score = 0.1

# -------- Final Trust Score (CORE FORMULA) --------
FINAL_TRUST_SCORE = (
    0.5 * emotion_score +
    0.3 * keystroke_score +
    0.2 * tab_score
)

# -------- Risk Classification --------
if FINAL_TRUST_SCORE >= 0.75:
    risk_level = "LOW"
elif FINAL_TRUST_SCORE >= 0.45:
    risk_level = "MEDIUM"
else:
    risk_level = "HIGH"

# ================= DISPLAY METRICS =================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Emotion Trust", round(emotion_score, 2))

with col2:
    st.metric("Keystroke Trust", round(keystroke_score, 2))

with col3:
    st.metric("Tab Discipline", round(tab_score, 2))

st.divider()

st.metric("🎯 Final Trust Score", round(FINAL_TRUST_SCORE, 2))

if risk_level == "LOW":
    st.success("🟢 Low Risk Candidate")
elif risk_level == "MEDIUM":
    st.warning("🟡 Medium Risk Candidate")
else:
    st.error("🔴 High Risk Candidate")

# ================= FINAL STATUS =================
st.success("✅ Exam Completed Successfully")
