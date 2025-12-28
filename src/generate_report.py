"""
generate_report.py
Purpose:
Generate final AI proctoring report from SQLite logs
Aligned with enhanced Streamlit proctoring system
"""

import sqlite3
import pandas as pd
import ast
import numpy as np
from collections import Counter, defaultdict

# -------------------- CONFIG --------------------
DB_PATH = "logs/proctoring_logs.db"   # Update if different

# -------------------- LOAD DATA --------------------
try:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM proctoring_logs", conn)
    conn.close()
except Exception as e:
    print("❌ Unable to read database:", e)
    exit()

# -------------------- VALIDATION --------------------
if df.empty:
    print("⚠ No monitoring data found.")
    print("👉 Please run the Streamlit proctoring session first.")
    exit()

print("\n📄 AI PROCTORING FINAL REPORT")
print("=" * 75)

# -------------------- TIME ANALYSIS --------------------
start_time = df["time"].min()
end_time = df["time"].max()
duration = int(end_time - start_time)

# -------------------- FACE ANALYSIS --------------------
multiple_faces = (df["faces"] > 1).sum()
no_face = (df["faces"] == 0).sum()

# -------------------- OBJECT ANALYSIS --------------------
obj_counter = Counter()
confidence_map = defaultdict(list)
malpractice_events = 0

for _, row in df.iterrows():
    # Parse objects
    try:
        objects = ast.literal_eval(row["objects"]) if row["objects"] else []
    except Exception:
        objects = []

    try:
        confidences = ast.literal_eval(row["confidences"]) if row["confidences"] else []
    except Exception:
        confidences = []

    if row.get("malpractice", 0) == 1:
        malpractice_events += 1

    for obj, conf in zip(objects, confidences):
        obj_counter[obj] += 1
        confidence_map[obj].append(conf)

# -------------------- REPORT OUTPUT --------------------
print("\n📊 SESSION SUMMARY")
print("-" * 75)
print(f"⏱ Session Duration        : {duration} seconds")
print(f"👤 Multiple Faces Detected : {multiple_faces} time(s)")
print(f"🚫 No Face Detected        : {no_face} time(s)")
print(f"📵 Malpractice Events     : {malpractice_events} time(s)")

# -------------------- DEVICE DETAILS --------------------
print("\n📱 MALPRACTICE DEVICE DETECTION")
print("-" * 75)

if obj_counter:
    for obj, count in obj_counter.items():
        avg_conf = np.mean(confidence_map[obj])
        print(
            f"- {obj.upper():<12} → Detected {count} time(s), "
            f"Avg Confidence: {avg_conf:.2f}"
        )
else:
    print("✅ No electronic devices detected during the session.")

# -------------------- FINAL VERDICT --------------------
print("\n🧠 CANDIDATE CONFIDENCE VERDICT")
print("-" * 75)

if multiple_faces == 0 and no_face == 0 and malpractice_events == 0:
    confidence_score = round(1 - (len(df) * 0.001), 2)
    confidence_score = max(confidence_score, 0.85)

    print("✅ STATUS : CLEAN SESSION")
    print(f"📊 Confidence Score : {confidence_score}")
    print("✔ Single face maintained")
    print("✔ No device detected")
    print("✔ Continuous presence")
    print("🎯 Candidate is CONFIDENT – No malpractice detected")

else:
    print("🚨 STATUS : MALPRACTICE / IRREGULARITY DETECTED")

    if multiple_faces > 0:
        print(f"⚠ Multiple faces observed : {multiple_faces} time(s)")

    if no_face > 0:
        print(f"⚠ Candidate absent from frame : {no_face} time(s)")

    if malpractice_events > 0:
        print(f"⚠ Electronic device detected : {malpractice_events} time(s)")

    print("❗ Manual review recommended")

# -------------------- FOOTER --------------------
print("\nℹ Notes:")
print("- Confidence is calculated post-session only")
print("- Even small phone detections are treated as malpractice")
print("- Report is auto-generated from backend inference logs")

print("\n✔ Report generation completed successfully.")
