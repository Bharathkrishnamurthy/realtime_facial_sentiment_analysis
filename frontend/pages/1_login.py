import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.auth.login import validate_login
from src.session.session_manager import create_session

st.title("Candidate Login")

name = st.text_input("Name")
password = st.text_input("Password", type="password")
college = st.text_input("College")
experience = st.radio("Experience", ["Fresher", "Experienced"])

if st.button("Start Exam"):
    if validate_login(name, password, college, experience):
        session_id = create_session({
            "name": name,
            "college": college,
            "experience": experience
        })

        st.session_state["session_id"] = session_id
        st.success("Monitoring Started 📹")
        st.switch_page("pages/2_Exam.py")
