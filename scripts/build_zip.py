import zipfile
import os
import shutil

DIST = "dist"
ZIP_NAME = "LifeRPG_full.zip"

exe_path = None

for root, _, files in os.walk("dist"):
    if "LifeRPG.exe" in files:
        exe_path = os.path.join(root, "LifeRPG.exe")
        break

if not exe_path:
    raise RuntimeError("LifeRPG.exe not found")

zip_path = os.path.join(DIST, ZIP_NAME)

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(exe_path, "LifeRPG.exe")
    z.write(os.path.join(DIST, "manifest.json"), "manifest.json")

print("ZIP built:", zip_path)
