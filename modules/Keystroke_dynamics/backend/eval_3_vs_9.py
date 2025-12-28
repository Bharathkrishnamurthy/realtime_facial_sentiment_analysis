# backend/eval_3_vs_9.py
"""
Evaluate baseline 3-feature model vs full 9-feature model
using data stored in keystroke_samples.

Usage (from backend folder):
  python eval_3_vs_9.py <user_id>
"""

import sys
import json
import math
import statistics
from app.database import get_conn
from app.feature_extractor import extract_features

# --- make sure the table exists (safe if already there) ---
SAMPLES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS keystroke_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  session_id TEXT,
  phase TEXT,
  enrollment INTEGER,
  question_id TEXT,
  events_json TEXT,
  meta_json TEXT,
  score REAL,
  verdict TEXT,
  paste_flag INTEGER,
  created_at INTEGER
);
"""

def ensure_samples_table():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(SAMPLES_TABLE_SQL)
    conn.commit()

# baseline uses 3 dims from the feature_vector: indices 0, 2, 6
BASE_IDX = [0, 2, 6]  # e.g. mean dwell, mean flight, typing speed (example mapping)

# simple gaussian distance -> score in [0, 100]
def score_gaussian(vec, mean, std, alpha=0.6, eps=1e-6):
    v = list(vec)
    m = list(mean)
    s = list(std)
    d = 0.0
    for i in range(len(v)):
        z = (v[i] - m[i]) / (s[i] + eps)
        d += z * z
    return 100.0 * math.exp(-alpha * d)


def mean_std(vectors):
    if not vectors:
        raise ValueError("Empty vector list")
    dim = len(vectors[0])
    means = []
    stds = []
    for i in range(dim):
        vals = [v[i] for v in vectors]
        means.append(statistics.mean(vals))
        stds.append(statistics.pstdev(vals) or 1.0)
    return means, stds


def load_vectors_for_user(user_id, max_samples=None):
    """
    Load events for a user from keystroke_samples,
    recompute feature_vector for each using extract_features().
    Returns list of feature vectors.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT events_json
        FROM keystroke_samples
        WHERE user_id = ?
        ORDER BY created_at
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    if max_samples:
        rows = rows[:max_samples]

    vectors = []
    for (events_json,) in rows:
        events = json.loads(events_json)
        res = extract_features(events)
        if isinstance(res, dict):
            fv = res.get("feature_vector")
        else:
            fv = getattr(res, "feature_vector", None)
        if fv is None:
            continue
        vectors.append(list(fv))
    return vectors


def main():
    if len(sys.argv) < 2:
        print("Usage: python eval_3_vs_9.py <user_id>")
        sys.exit(1)

    user_id = sys.argv[1]
    print(f"Evaluating user: {user_id}")

    # ensure table exists before selecting
    ensure_samples_table()

    # load all vectors, use first N for enroll, next M for test
    all_vecs = load_vectors_for_user(user_id)
    if len(all_vecs) < 15:
        print(f"Not enough samples for robust eval (have {len(all_vecs)}, need >= 15).")
        return

    n_enroll = 7
    n_test = 10
    enroll_vecs = all_vecs[:n_enroll]
    test_vecs = all_vecs[n_enroll:n_enroll + n_test]

    # full 9-feature stats
    mean_full, std_full = mean_std(enroll_vecs)

    # baseline 3-feature stats
    enroll_base = [[v[i] for i in BASE_IDX] for v in enroll_vecs]
    test_base = [[v[i] for i in BASE_IDX] for v in test_vecs]
    mean_base, std_base = mean_std(enroll_base)

    print("Sample\tBaseScore\tFullScore")
    for idx, (bvec, fvec) in enumerate(zip(test_base, test_vecs), start=1):
        s_base = score_gaussian(bvec, mean_base, std_base)
        s_full = score_gaussian(fvec, mean_full, std_full)
        print(f"{idx}\t{s_base:6.2f}\t\t{s_full:6.2f}")


if __name__ == "__main__":
    main()
