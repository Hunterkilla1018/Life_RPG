import hashlib
import json
import os

DIST = "dist"
EXE = "LifeRPG.exe"
OUT = os.path.join(DIST, "manifest.json")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

exe_path = None

for root, _, files in os.walk("dist"):
    if EXE in files:
        exe_path = os.path.join(root, EXE)
        break

if not exe_path:
    raise RuntimeError("LifeRPG.exe not found")

manifest = {
    "files": {
        EXE: sha256(exe_path)
    }
}

os.makedirs(DIST, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=4)

print("Manifest generated")
