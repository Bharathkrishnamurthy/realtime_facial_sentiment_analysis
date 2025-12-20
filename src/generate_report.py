# generate_report.py
# Purpose: Generate final proctoring report from SQLite logs

import sqlite3
import pandas as pd
from collections import Counter
import ast
import numpy as np

DB_PATH = "logs/emotion_logs.db"

# ---------------- CONNECT ----------------
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT * FROM emotion_logs", conn)
conn.close()

# ---------------- VALIDATION ----------------
if df.empty:
    print("⚠ No monitoring data found.")
    print("👉 Please run the Streamlit proctoring app first.")
    exit()

print("\n📄 PROCTORING REPORT")
print("=" * 60)

# ---------------- SESSION SUMMARY ----------------
duration = int(df["time"].max() - df["time"].min())

multiple_faces = (df["faces"] > 1).sum()
no_face = (df["faces"] == 0).sum()

print("\n📊 SESSION SUMMARY")
print(f"⏱ Session Duration        : {duration} seconds")
print(f"👤 Multiple Faces Detected : {multiple_faces} occurrence(s)")
print(f"🚫 No Face Detected        : {no_face} occurrence(s)")

# ---------------- OBJECT DETECTION ----------------
all_objects = []
confidence_map = {}
frame_confidences = []

multi_device_events = 0

for _, row in df.iterrows():
    objs_raw = row.get("objects", "")
    frame_conf = row.get("frame_confidence", 0.0)

    # Parse objects list safely
    try:
        objs = ast.literal_eval(objs_raw) if isinstance(objs_raw, str) else []
    except Exception:
        objs = []

    if len(set(objs)) > 1:
        multi_device_events += 1

    for o in objs:
        all_objects.append(o)

    if frame_conf and frame_conf > 0:
        frame_confidences.append(frame_conf)

obj_counter = Counter(all_objects)

# ---------------- DISPLAY OBJECT REPORT ----------------
print("\n📱 MALPRACTICE OBJECT DETECTION")

if obj_counter:
    for obj, count in obj_counter.items():
        print(f"- {obj.title():<12} → Detected {count} time(s)")
else:
    print("✅ No electronic devices detected during the session.")

print(f"\n🔁 Multiple Device Events  : {multi_device_events}")

# ---------------- OVERALL CONFIDENCE SUMMARY ----------------
print("\n📌 OVERALL DETECTION CONFIDENCE SUMMARY")

if frame_confidences:
    overall_confidence = float(np.mean(frame_confidences))
    print(f"📊 Overall Detection Confidence : {overall_confidence:.2f}")
    print(
        "📈 Confidence is computed as the average of frame-level object "
        "detection confidence scores across the entire monitoring session."
    )
else:
    print(
        "✅ No malpractice-related objects were detected, "
        "therefore overall detection confidence is not applicable."
    )

print("\n✔ Report generation completed successfully.")
