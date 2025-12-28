# debug_inspect.py
import sqlite3, numpy as np, sys, json
DB = "keystroke.db"

def load_embeddings(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT embedding FROM profiles WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    embs = []
    for r in rows:
        if r and r[0]:
            embs.append(np.frombuffer(r[0], dtype=np.float32))
    return embs

def cosine(a,b):
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    return 0.0 if na==0 or nb==0 else float(np.dot(a,b)/(na*nb))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_inspect.py <user_id>")
        sys.exit(1)
    uid = sys.argv[1]
    embs = load_embeddings(uid)
    print("Loaded", len(embs), "embeddings for", uid)
    if not embs:
        sys.exit(0)
    mean_t = np.mean(np.stack(embs), axis=0)
    print("Mean template (first 8 dims):", mean_t[:8].tolist())

    # print pairwise similarities
    for i,e in enumerate(embs):
        print(f"sim(template[{i}] , mean) = {cosine(e,mean_t):.4f}")
    # save mean for later inspection
    np.save(f"{uid}_mean_template.npy", mean_t)
    print("Saved mean template to", f"{uid}_mean_template.npy")
