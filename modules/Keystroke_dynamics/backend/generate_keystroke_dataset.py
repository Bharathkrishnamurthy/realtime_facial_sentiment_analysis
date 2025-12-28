import json, random, math, os, zipfile, statistics, uuid
from pathlib import Path

random.seed(42)

OUT_DIR = Path("keystroke_dataset")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PHRASES = [
    "The quick brown fox jumps over the lazy dog.",
    "Please describe yourself in two lines.",
    "Type this sentence exactly: The quick brown fox jumps over the lazy dog.",
    "I love coding and solving problems.",
    "Data science combines math, code, and domain knowledge.",
    "Typing rhythm can be a behavioral biometric.",
    "This is a demo of keystroke dynamics.",
    "Practice makes perfect; type carefully."
]

def gen_sample(phrase, paste_prob=0.03):
    events = []
    ts = 0.0
    base_hold_mean = random.uniform(80, 180)
    base_hold_sd = max(5.0, base_hold_mean * 0.18)
    base_flight_mean = random.uniform(80, 160)
    base_flight_sd = max(5.0, base_flight_mean * 0.25)

    kd_times = []
    ku_times = []

    for ch in phrase:
        kd_ts = ts
        hold = max(5.0, random.gauss(base_hold_mean, base_hold_sd))
        ku_ts = kd_ts + hold
        events.append({"type": "keydown", "key": ch, "ts": round(kd_ts, 3)})
        events.append({"type": "keyup", "key": ch, "ts": round(ku_ts, 3)})
        kd_times.append(kd_ts)
        ku_times.append(ku_ts)
        flight = max(5.0, random.gauss(base_flight_mean, base_flight_sd))
        ts = ku_ts + flight

    paste_flag = random.random() < paste_prob
    if paste_flag:
        idx = max(0, len(events)//2 - 1)
        events.insert(idx, {"type":"paste", "ts": round(max(0, events[idx]["ts"] - 1.0),3), "clipboardLength": len(phrase)})

    holds = [ku - kd for kd, ku in zip(kd_times, ku_times)]
    dd = [kd_times[i+1] - kd_times[i] for i in range(len(kd_times)-1)] if len(kd_times) > 1 else []
    duration = (events[-1]["ts"] - events[0]["ts"]) if events else 0.0
    chars = len(kd_times)
    cpm = (chars / duration) * 60000.0 if duration > 0 else 0.0
    pauses_over_200 = sum(1 for x in dd if x > 200.0)

    meta = {
        "mean_dwell": round(statistics.mean(holds),3),
        "mean_flight": round(statistics.mean(dd),3) if dd else 0.0,
        "cpm": round(cpm,3),
        "pauses_over_200": int(pauses_over_200),
        "duration_ms": round(duration,3),
        "num_key_events": len(events)
    }

    return {
        "id": str(uuid.uuid4()),
        "phrase": phrase,
        "events": events,
        "paste_flag": paste_flag,
        "meta": meta
    }

dataset = []
N = 500
for _ in range(N):
    phrase = random.choice(PHRASES)
    dataset.append(gen_sample(phrase))

json_path = OUT_DIR / "keystroke_samples_500.json"
with open(json_path, "w", encoding="utf8") as f:
    json.dump(dataset, f, indent=2)

print(f"Saved JSON dataset to: {json_path.resolve()}")
