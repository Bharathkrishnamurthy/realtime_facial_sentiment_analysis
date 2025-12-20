# object_detection.py
# Enhanced object detection module for AI proctoring

from ultralytics import YOLO
import numpy as np

# ---------------- LOAD MODEL ----------------
model = YOLO("yolov8n.pt")

# Objects treated as malpractice
BANNED_OBJECTS = {
    "cell phone",
    "laptop",
    "tablet",
    "headphones",
    "remote"
}

# ---------------- DETECTION FUNCTION ----------------
def detect_objects(frame_bgr, conf_threshold=0.5):
    """
    Detect malpractice-related electronic devices.

    Returns:
        result (dict):
            {
              "objects": list[str],
              "confidences": list[float],
              "boxes": list[(x1,y1,x2,y2)],
              "frame_confidence": float
            }
    """

    results = model(frame_bgr, conf=conf_threshold, verbose=False)[0]

    objects = []
    confidences = []
    boxes = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        confidence = float(box.conf[0])

        if label in BANNED_OBJECTS:
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            objects.append(label)
            confidences.append(confidence)
            boxes.append((x1, y1, x2, y2))

    # Frame-level confidence (robust average)
    frame_confidence = (
        float(np.mean(confidences)) if confidences else 0.0
    )

    return {
        "objects": objects,
        "confidences": confidences,
        "boxes": boxes,
        "frame_confidence": frame_confidence
    }
