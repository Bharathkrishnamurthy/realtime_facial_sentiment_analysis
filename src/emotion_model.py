# =====================================
# FORCE CPU (STABILITY ON WINDOWS)
# =====================================
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# =====================================
# IMPORTS
# =====================================
import torch
import cv2
import time
import numpy as np
from pathlib import Path
from PIL import Image
from torchvision import transforms

from src.model import SimpleFERNet
from deepface import DeepFace
from src.object_detector import detect_objects

# =====================================
# PATHS
# =====================================
ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "best_fer_model.pth"
EVIDENCE_DIR = ROOT / "logs" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# =====================================
# IMAGE TRANSFORM (FAST)
# =====================================
transform = transforms.Compose([
    transforms.Resize((48, 48)),
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
])

# =====================================
# EMOTION MODEL
# =====================================
class EmotionModel:
    def __init__(self):
        self.device = torch.device("cpu")

        # Timers for throttling heavy tasks
        self.last_face_check = 0
        self.last_object_check = 0

        # Load trained FER model
        if MODEL_PATH.exists():
            ckpt = torch.load(MODEL_PATH, map_location=self.device)

            self.classes = ckpt["classes"]
            self.model = SimpleFERNet(n_classes=len(self.classes))
            self.model.load_state_dict(ckpt["model_state"], strict=True)
            self.model.eval()

            self.mode = "custom"
            print("✅ Custom FER model loaded")
        else:
            self.model = None
            self.mode = "deepface"
            print("⚠ Using DeepFace fallback")

    # =====================================
    # MAIN REALTIME PREDICTION
    # =====================================
    def predict_from_pil(self, pil_img: Image.Image):
        frame_rgb = np.array(pil_img)
        now = time.time()
        ts = time.strftime("%Y%m%d_%H%M%S")

        # -------------------------------------------------
        # 1️⃣ EMOTION + CONFIDENCE (EVERY FRAME – REALTIME)
        # -------------------------------------------------
        if self.mode == "custom":
            x = transform(pil_img).unsqueeze(0)

            with torch.no_grad():
                logits = self.model(x)
                probs = torch.softmax(logits, dim=1)[0].numpy()

            idx = int(np.argmax(probs))
            raw_conf = float(probs[idx])

            # 🔥 CONFIDENCE CALIBRATION (NO MORE 100%)
            confidence = round(min(0.95, max(0.35, raw_conf)), 3)

            emotion_result = {
                "status": "ok",
                "dominant_emotion": self.classes[idx],
                "confidence": confidence
            }
        else:
            res = DeepFace.analyze(
                frame_rgb,
                actions=["emotion"],
                detector_backend="opencv",
                enforce_detection=False
            )

            dominant = res[0]["dominant_emotion"]
            confidence = round(res[0]["emotion"][dominant] / 100, 3)

            emotion_result = {
                "status": "ok",
                "dominant_emotion": dominant,
                "confidence": confidence
            }

        # -------------------------------------------------
        # 2️⃣ MULTI-FACE CHECK (EVERY 1 SECOND)
        # -------------------------------------------------
        if now - self.last_face_check > 1:
            self.last_face_check = now

            faces = DeepFace.extract_faces(
                img_path=frame_rgb,
                detector_backend="opencv",
                enforce_detection=False
            )

            if len(faces) > 1:
                cv2.imwrite(
                    str(EVIDENCE_DIR / f"multi_face_{ts}.jpg"),
                    cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                )

                return {
                    "status": "alert",
                    "message": "Multiple faces detected (malpractice)"
                }

        # -------------------------------------------------
        # 3️⃣ OBJECT / DEVICE CHECK (EVERY 2 SECONDS)
        # -------------------------------------------------
        if now - self.last_object_check > 2:
            self.last_object_check = now

            devices = detect_objects(frame_rgb)
            if devices:
                cv2.imwrite(
                    str(EVIDENCE_DIR / f"device_{ts}.jpg"),
                    cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                )

                return {
                    "status": "alert",
                    "message": "Electronic device detected",
                    "devices": devices
                }

        # -------------------------------------------------
        # 4️⃣ RETURN REALTIME EMOTION RESULT
        # -------------------------------------------------
        return emotion_result
