# src/dataset.py
import cv2, os
from pathlib import Path
from PIL import Image
import numpy as np

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

def detect_and_crop_face(img_path, out_size=(48,48)):
    img = cv2.imread(str(img_path))
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if len(faces) == 0:
        return None
    # pick largest face
    x,y,w,h = max(faces, key=lambda b: b[2]*b[3])
    face = img[y:y+h, x:x+w]
    face = cv2.resize(face, out_size)
    # convert BGR -> RGB
    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
    return Image.fromarray(face)

def preprocess_folder(input_dir, output_dir, out_size=(48,48)):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for cls in [d for d in input_dir.iterdir() if d.is_dir()]:
        out_class_dir = output_dir / cls.name
        out_class_dir.mkdir(parents=True, exist_ok=True)
        for img_path in cls.glob('*'):
            try:
                face_img = detect_and_crop_face(img_path, out_size)
                if face_img:
                    face_img.save(out_class_dir / img_path.name)
            except Exception as e:
                print("Error", img_path, e)
