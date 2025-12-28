# app/matcher.py
import numpy as np
from .config import ACCEPT_THRESHOLD, REVIEW_THRESHOLD

def bytes_to_vector(b):
    if b is None:
        return None
    try:
        return np.frombuffer(b, dtype=np.float32)
    except Exception:
        try:
            return np.frombuffer(bytes(b), dtype=np.float32)
        except Exception:
            return None

def cosine_similarity(a, b):
    if a is None or b is None:
        return 0.0
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))

def decide_score_and_verdict(feature_vector, templates, paste_flag):
    """
    Mean-template matcher using cosine similarity.

    templates: list of numpy arrays (stored embeddings)
    feature_vector: numpy array for current sample
    paste_flag: bool (from extractor)
    """
    if not templates:
        return {"score": 0.0, "verdict": "no_template"}

    clean = [t for t in templates if t is not None and t.size == feature_vector.size]
    if not clean:
        return {"score": 0.0, "verdict": "no_template"}

    mean_t = np.mean(np.stack(clean, axis=0), axis=0)
    score = cosine_similarity(feature_vector, mean_t)

    # Malpractice override
    if paste_flag:
        return {"score": score, "verdict": "suspicious_paste"}

    # Thresholds from config (professional touch)
    if score >= ACCEPT_THRESHOLD:
        return {"score": score, "verdict": "accepted"}
    elif score >= REVIEW_THRESHOLD:
        return {"score": score, "verdict": "review"}
    else:
        return {"score": score, "verdict": "rejected"}
