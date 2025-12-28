from src.emotion_model import EmotionModel
from src.object_detector import ObjectDetector
import time

emotion_model = EmotionModel()
object_model = ObjectDetector()

def monitor(frame, session):
    emotion = emotion_model.predict(frame)
    objects = object_model.detect(frame)

    session["emotion_log"].append({
        "time": time.time(),
        "emotion": emotion
    })

    if "cell phone" in objects or len(objects) > 1:
        session["malpractice"] += 1
