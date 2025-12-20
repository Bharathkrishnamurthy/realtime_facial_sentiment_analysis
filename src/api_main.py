from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from src.emotion_model import EmotionModel
from PIL import Image
import io, sqlite3, time, cv2
from pathlib import Path
import pandas as pd

app = FastAPI()

# =========================
# PATHS & DB
# =========================
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "logs" / "emotion_logs.db"
LOGS = ROOT / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

# =========================
# DB INIT (MIGRATION SAFE)
# =========================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS emotion_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source TEXT,
            emotion TEXT,
            confidence REAL
        )
    """)

    c.execute("PRAGMA table_info(emotion_logs)")
    cols = [x[1] for x in c.fetchall()]

    if "emotion" not in cols:
        c.execute("ALTER TABLE emotion_logs ADD COLUMN emotion TEXT")
    if "confidence" not in cols:
        c.execute("ALTER TABLE emotion_logs ADD COLUMN confidence REAL")

    conn.commit()
    conn.close()

init_db()

# =========================
# LOAD MODEL ONCE
# =========================
model = EmotionModel()
print("✅ Emotion model ready")

# =========================
# DB SAVE
# =========================
def save_to_db(emotion, confidence, source="webcam"):
    conn = sqlite3.connect(DB, check_same_thread=False)
    c = conn.cursor()
    c.execute(
        "INSERT INTO emotion_logs (timestamp, source, emotion, confidence) VALUES (?, ?, ?, ?)",
        (time.strftime("%Y-%m-%d %H:%M:%S"), source, emotion, confidence)
    )
    conn.commit()
    conn.close()

# =========================
# IMAGE FRAME API
# =========================
@app.post("/api/emotion/frame")
async def detect_frame(
    file: UploadFile = File(...),
    bg: BackgroundTasks = BackgroundTasks()
):
    img = Image.open(io.BytesIO(await file.read())).convert("RGB")
    result = model.predict_from_pil(img)

    if result["status"] == "ok":
        bg.add_task(save_to_db, result["dominant_emotion"], result["confidence"])

    return result

# =========================
# VIDEO ANALYSIS API
# =========================
@app.post("/api/emotion/video")
async def analyze_video(file: UploadFile = File(...)):
    video_path = LOGS / file.filename
    with open(video_path, "wb") as f:
        f.write(await file.read())

    cap = cv2.VideoCapture(str(video_path))
    frame_id = 0
    analyzed = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % 15 == 0:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            res = model.predict_from_pil(img)

            if res["status"] == "ok":
                save_to_db(res["dominant_emotion"], res["confidence"], "video")
                analyzed += 1

        frame_id += 1

    cap.release()
    return {"status": "ok", "frames_analyzed": analyzed}

# =========================
# DOWNLOAD REPORT
# =========================
@app.get("/api/report/download")
def download_report():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM emotion_logs", conn)
    path = LOGS / "emotion_report.csv"
    df.to_csv(path, index=False)
    return FileResponse(path, filename="emotion_report.csv")
