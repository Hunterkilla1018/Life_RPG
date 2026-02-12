import os
import json
import hashlib

DIST_DIR = "dist"
OUTPUT = "manifest.json"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


if not os.path.exists(DIST_DIR):
    raise RuntimeError("dist folder not found")

manifest = {
    "version": "AUTO",
    "files": {}
}

# Detect build mode automatically
for item in os.listdir(DIST_DIR):

    item_path = os.path.join(DIST_DIR, item)

    # Skip launcher exe
    if item.startswith("LifeRPG_Launcher"):
        continue

    # If folder build
    if os.path.isdir(item_path):
        for root, dirs, files in os.walk(item_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, item_path)
                rel_path = rel_path.replace("\\", "/")
                manifest["files"][rel_path] = sha256(full_path)

    # If onefile build (exe directly in dist)
    elif item.endswith(".exe"):
        manifest["files"][item] = sha256(item_path)

if not manifest["files"]:
    raise RuntimeError("No game files detected in dist folder")

with open(OUTPUT, "w") as f:
    json.dump(manifest, f, indent=4)

print("manifest.json generated successfully.")
