import importlib

try:
    m = importlib.import_module("app.main")
    print("Imported:", m)
    print("Has attribute 'app'? ->", hasattr(m, "app"))
    print("app object:", getattr(m, "app", None))
except Exception as e:
    print("ERROR:", e)
