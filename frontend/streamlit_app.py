import streamlit as st
import cv2
import time
import numpy as np
from collections import Counter, defaultdict
from ultralytics import YOLO

# -------------------- CONFIG --------------------
st.set_page_config(page_title="AI Proctoring System", layout="wide")

CONF_THRESHOLD = 0.5
MAL_OBJECTS = ["cell phone", "laptop", "tablet"]

# -------------------- LOAD MODELS --------------------
@st.cache_resource
def load_models():
    face = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    yolo = YOLO("yolov8n.pt")
    return face, yolo

face_detector, yolo_model = load_models()

# -------------------- SESSION STATE --------------------
if "logs" not in st.session_state:
    st.session_state.logs = []

if "running" not in st.session_state:
    st.session_state.running = False

# -------------------- UI --------------------
st.title("🛡️ Real-Time AI Proctoring System")

col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("🎛️ Controls")
    start = st.button("▶ Start Monitoring")
    stop = st.button("⏹ Stop & Generate Report")

# -------------------- START SESSION --------------------
if start:
    st.session_state.running = True
    st.session_state.logs = []
    st.session_state.start_time = time.time()

# -------------------- VIDEO STREAM --------------------
if st.session_state.running:
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    frame_window = col1.empty()

    while st.session_state.running:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = time.time()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 5)

        # -------- FACE BOXES (NO TEXT, NO CONFIDENCE) --------
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)

        # -------- OBJECT DETECTION --------
        results = yolo_model(frame, conf=CONF_THRESHOLD, verbose=False)[0]

        detected_objects = []
        detected_confidences = []

        for box in results.boxes:
            cls = int(box.cls[0])
            label = yolo_model.names[cls]
            conf = float(box.conf[0])

            if label in MAL_OBJECTS:
                detected_objects.append(label)
                detected_confidences.append(conf)

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

        # -------- LOGGING (BACKEND ONLY) --------
        st.session_state.logs.append({
            "time": timestamp,
            "faces": len(faces),
            "objects": detected_objects,
            "confidences": detected_confidences
        })

        frame_window.image(frame, channels="BGR")

        if stop:
            st.session_state.running = False
            break

    cap.release()

# -------------------- REPORT SECTION --------------------
if not st.session_state.running and st.session_state.logs:
    st.divider()
    st.header("📄 Proctoring Report")

    logs = st.session_state.logs
    duration = int(time.time() - st.session_state.start_time)

    # -------- FACE ANALYSIS --------
    multiple_faces = sum(1 for l in logs if l["faces"] > 1)
    no_face = sum(1 for l in logs if l["faces"] == 0)

    # -------- OBJECT + CONFIDENCE ANALYSIS --------
    obj_counter = Counter()
    confidence_map = defaultdict(list)
    multi_device_events = 0

    for l in logs:
        objs = l["objects"]
        confs = l["confidences"]

        if len(set(objs)) > 1:
            multi_device_events += 1

        for o, c in zip(objs, confs):
            obj_counter[o] += 1
            confidence_map[o].append(c)

    # -------- DISPLAY REPORT --------
    st.subheader("📊 Session Summary")
    st.write(f"⏱ Duration: **{duration} seconds**")
    st.write(f"👤 Multiple faces detected: **{multiple_faces} times**")
    st.write(f"🚫 No face detected: **{no_face} times**")

    st.subheader("📱 Malpractice Object Detection (with Confidence)")

    if obj_counter:
        for obj, count in obj_counter.items():
            avg_conf = np.mean(confidence_map[obj])
            st.write(
                f"**{obj}** → Detected **{count} times**, "
                f"Average Confidence: **{avg_conf:.2f}**"
            )
    else:
        st.write("✅ No electronic devices detected.")

    st.write(f"🔁 Multiple device events: **{multi_device_events}**")

    st.info(
        "Confidence scores were intentionally hidden during live monitoring. "
        "All confidence values shown here are aggregated from backend inference "
        "to avoid bias and misleading real-time interpretation."
    )
