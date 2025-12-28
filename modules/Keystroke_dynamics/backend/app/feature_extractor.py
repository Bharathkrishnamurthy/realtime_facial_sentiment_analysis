# app/feature_extractor.py
import numpy as np
import math

def safe_div(a, b):
    return a / b if b else 0.0

def extract_features(events):
    """
    Feature extractor with improved paste detection and blur/focus counting.

    Returns:
      {
        feature_vector: np.ndarray (64),
        paste_flag: bool,
        meta: {...}
      }
    """
    if not events:
        return {"feature_vector": np.zeros(64, dtype=np.float32), "paste_flag": False, "meta": {}}

    # copy and compute relative times
    base_ts = events[0].get("ts", 0)
    for e in events:
        e["rts"] = e.get("ts", 0) - base_ts

    # classify events
    keydowns = [e for e in events if e.get("type") == "keydown"]
    keyups = [e for e in events if e.get("type") == "keyup"]
    paste_events = [e for e in events if e.get("type") == "paste"]
    blur_events = [e for e in events if e.get("type") == "blur"]
    focus_events = [e for e in events if e.get("type") == "focus"]

    # hold times mapping keydown->next keyup for same key (simple greedy)
    holds = []
    ku_idx = 0
    for kd in keydowns:
        kd_ts = kd.get("rts", 0.0)
        matched = None
        while ku_idx < len(keyups):
            ku = keyups[ku_idx]
            ku_idx += 1
            if ku.get("rts", 0.0) >= kd_ts:
                matched = ku
                break
        if matched:
            ht = matched.get("rts", 0.0) - kd_ts
            if ht < 0:
                ht = 0.0
            holds.append(float(ht))
    if not holds:
        holds = [0.0]

    # digraphs dd between successive keydowns
    dd_list = []
    for i in range(len(keydowns) - 1):
        dd = keydowns[i+1].get("rts", 0.0) - keydowns[i].get("rts", 0.0)
        dd_list.append(float(max(0.0, dd)))
    if not dd_list:
        dd_list = [0.0]

    holds_arr = np.array(holds, dtype=np.float32)
    dd_arr = np.array(dd_list, dtype=np.float32)

    median_ht = float(np.median(holds_arr))
    mad_ht = float(np.median(np.abs(holds_arr - median_ht))) if holds_arr.size > 0 else 0.0
    median_dd = float(np.median(dd_arr))
    mad_dd = float(np.median(np.abs(dd_arr - median_dd))) if dd_arr.size > 0 else 0.0

    duration = events[-1].get("rts", 0.0) - events[0].get("rts", 0.0)
    char_key_events = len([e for e in events if e.get("type") in ("keydown","keyup")])
    cpm = (char_key_events / duration) * 60000.0 if duration > 0 else 0.0
    pauses_over_200 = sum(1 for x in dd_list if x > 200.0)

    # --- Paste heuristics ---
    paste_flag = False
    # explicit paste events
    if paste_events:
        paste_flag = True
    # heuristic: if last action contains a long insertion and there were very few key events
    # look for event objects with clipboardLength (some clients send it)
    clipboard_lengths = [e.get("clipboardLength") for e in events if e.get("clipboardLength")]
    if clipboard_lengths:
        # inserted text length far larger than key events -> likely paste
        if max(clipboard_lengths) > max(5, 3 * char_key_events):
            paste_flag = True

    # heuristic: detect sudden large delta in text length (if events include pos/selLen)
    # compute approximate typed length derived from keydown/keyup counts vs last explicit textLen if provided
    text_lengths = [e.get("textLen") for e in events if e.get("textLen") is not None]
    if text_lengths:
        # if text grew by large jump but few key events -> paste
        if len(text_lengths) >= 2:
            if (text_lengths[-1] - text_lengths[-2]) > max(10, 5 * char_key_events):
                paste_flag = True

    # --- Build 64-d vector like before ---
    vec = np.zeros(64, dtype=np.float32)
    vec[0] = median_ht
    vec[1] = mad_ht
    vec[2] = median_dd
    vec[3] = mad_dd
    vec[4] = math.log1p(cpm)
    vec[5] = float(pauses_over_200)
    vec[6] = float(len(holds))
    vec[7] = safe_div(median_ht, median_dd)

    vec[0:5] = vec[0:5] / np.array([2000.0, 2000.0, 2000.0, 2000.0, 10.0], dtype=np.float32)

    norm = np.linalg.norm(vec)
    if norm == 0:
        norm = 1.0
    vec = vec / norm

    meta = {
        "median_ht": median_ht,
        "mad_ht": mad_ht,
        "median_dd": median_dd,
        "mad_dd": mad_dd,
        "cpm": cpm,
        "pauses_over_200": pauses_over_200,
        "chars": char_key_events,
        "duration_ms": duration,
        "paste_detected_explicit": bool(paste_events),
        "paste_detected_heuristic": paste_flag and not bool(paste_events),
        "blur_count": len(blur_events),
        "focus_count": len(focus_events),
        "sample_hold_times": holds[:32],
        "sample_dd_times": dd_list[:32],
    }

    return {"feature_vector": vec.astype(np.float32), "paste_flag": paste_flag, "meta": meta}
