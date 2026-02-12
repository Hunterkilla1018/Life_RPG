import os
import json
import hashlib

BUILD_DIR = "dist"   # folder where your built game lives
OUTPUT = "manifest.json"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

manifest = {
    "version": "AUTO",
    "files": {}
}

for root, dirs, files in os.walk(BUILD_DIR):
    for file in files:
        full_path = os.path.join(root, file)
        rel_path = os.path.relpath(full_path, BUILD_DIR)
        manifest["files"][rel_path.replace("\\", "/")] = sha256(full_path)

with open(OUTPUT, "w") as f:
    json.dump(manifest, f, indent=4)

print("manifest.json generated.")
