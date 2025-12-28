# backend/test_create_user.py
import requests, json
try:
    r = requests.post("http://127.0.0.1:9000/api/create_user", json={"name": "Jayashree"}, timeout=5)
    print("Status:", r.status_code)
    print("Body:", r.text)
except Exception as e:
    print("Request failed:", repr(e))
