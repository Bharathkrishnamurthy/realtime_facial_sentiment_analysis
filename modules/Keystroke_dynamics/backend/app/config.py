# app/config.py
import os

# name of sqlite DB file located at backend/<DB_NAME>
DB_NAME = "keystroke_new.db"

# Enrollment rules (tuneable via env)
MIN_ENROLL_CHARS = int(os.getenv("KS_MIN_ENROLL_CHARS", "40"))
MIN_ENROLL_KEY_EVENTS = int(os.getenv("KS_MIN_ENROLL_KEY_EVENTS", "60"))

# Matcher thresholds
ACCEPT_THRESHOLD = float(os.getenv("KS_ACCEPT_T", "0.70"))
REVIEW_THRESHOLD = float(os.getenv("KS_REVIEW_T", "0.55"))

# Model label
MODEL_VERSION = os.getenv("KS_MODEL_VERSION", "ks_v1_robust64")
