import streamlit as st
import cv2
import time
import numpy as np
from collections import Counter, defaultdict
from ultralytics import YOLO

# -------------------- CONFIG --------------------
st.set_page_config(
    page_title="AI Proctoring System",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CONF_THRESHOLD = 0.25   # LOWERED → detect small phones
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
st.markdown(
    "<h1 style='text-align:center'>🛡️ Real-Time AI Proctoring System</h1>",
    unsafe_allow_html=True
)

col1, col2 = st.columns([3, 1])

with col2:
    st.subheader("🎛 Controls")
    start = st.button("▶ Start Monitoring", use_container_width=True)
    stop = st.button("⏹ Stop & Generate Report", use_container_width=True)

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

        frame = cv2.resize(frame, (1280, 720))  # FULL SCREEN EFFECT
        timestamp = time.time()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 5)

        # -------- FACE BOXES --------
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)

        # -------- OBJECT DETECTION --------
        results = yolo_model(frame, conf=CONF_THRESHOLD, verbose=False)[0]

        detected_objects = []
        detected_confidences = []
        malpractice_flag = False

        for box in results.boxes:
            cls = int(box.cls[0])
            label = yolo_model.names[cls]
            conf = float(box.conf[0])

            if label in MAL_OBJECTS:
                malpractice_flag = True
                detected_objects.append(label)
                detected_confidences.append(conf)

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

        # -------- MALPRACTICE ALERT (LIVE) --------
        if malpractice_flag:
            cv2.putText(
                frame,
                "📵 MALPRACTICE: PHONE / DEVICE DETECTED",
                (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.1,
                (0, 0, 255),
                3
            )

        # -------- LOGGING --------
        st.session_state.logs.append({
            "time": timestamp,
            "faces": len(faces),
            "objects": detected_objects,
            "confidences": detected_confidences,
            "malpractice": malpractice_flag
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

    multiple_faces = sum(1 for l in logs if l["faces"] > 1)
    no_face = sum(1 for l in logs if l["faces"] == 0)
    malpractice_events = sum(1 for l in logs if l["malpractice"])

    obj_counter = Counter()
    confidence_map = defaultdict(list)

    for l in logs:
        for o, c in zip(l["objects"], l["confidences"]):
            obj_counter[o] += 1
            confidence_map[o].append(c)

    # -------- SUMMARY --------
    st.subheader("📊 Session Summary")
    st.write(f"⏱ Duration: **{duration} seconds**")
    st.write(f"👤 Multiple Faces Detected: **{multiple_faces} times**")
    st.write(f"🚫 No Face Detected: **{no_face} times**")
    st.write(f"📵 Malpractice Events: **{malpractice_events} times**")

    # -------- OBJECT DETAILS --------
    st.subheader("📱 Device Detection Analysis")

    if obj_counter:
        for obj, count in obj_counter.items():
            avg_conf = np.mean(confidence_map[obj])
            st.write(
                f"**{obj.upper()}** → Detected **{count} times**, "
                f"Avg Confidence: **{avg_conf:.2f}**"
            )
    else:
        st.success("✅ No electronic devices detected")

    # -------- CONFIDENCE VERDICT --------
    st.subheader("🧠 Candidate Confidence Verdict")

    if multiple_faces == 0 and no_face == 0 and malpractice_events == 0:
        confidence_score = round(
            1 - (len(logs) * 0.001), 2
        )
        st.success(
            f"✅ Candidate is CONFIDENT\n\n"
            f"📊 Confidence Score: **{confidence_score}**\n\n"
            f"✔ No malpractice\n"
            f"✔ Single face throughout\n"
            f"✔ Continuous presence"
        )
    else:
        st.error(
            "🚨 Candidate behavior indicates MALPRACTICE or IRREGULARITIES.\n\n"
            "Please review flagged timestamps."
        )

    st.info(
        "Confidence values are computed post-session only "
        "to avoid real-time bias."
    )
