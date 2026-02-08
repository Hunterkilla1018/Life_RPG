import os
import sys
import time
import json
import zipfile
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request
import tempfile

# =====================================================
# VERSIONING
# =====================================================
APP_NAME = "LifeRPG"
APP_VERSION = "1.1.7"
VERSION_FILE = "version.txt"
GITHUB_REPO = "Hunterkilla1018/Life_RPG"

# =====================================================
# PATHS (SOURCE OF TRUTH)
# =====================================================
APPDATA_DIR = os.path.join(os.getenv("APPDATA"), "LifeRPG")
LAUNCHER_CONFIG = os.path.join(APPDATA_DIR, "launcher.json")
BASE_DIR = os.path.dirname(sys.executable)

# =====================================================
# FILES TO INSTALL
# =====================================================
FILES = {
    VERSION_FILE: APP_VERSION
}

# =====================================================
# INSTALL STATE (LOCKED LOGIC)
# =====================================================
def is_installed():
    return os.path.exists(LAUNCHER_CONFIG)

def ensure_appdata():
    os.makedirs(APPDATA_DIR, exist_ok=True)

def save_launcher_config(data):
    ensure_appdata()
    with open(LAUNCHER_CONFIG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_launcher_config():
    try:
        with open(LAUNCHER_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

# =====================================================
# VERSION / UPDATE HELPERS
# =====================================================
def read_installed_version():
    try:
        with open(os.path.join(BASE_DIR, VERSION_FILE), "r") as f:
            return f.read().strip()
    except Exception:
        return None

def get_latest_release():
    with urllib.request.urlopen(
        f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
        timeout=5
    ) as r:
        return json.loads(r.read().decode())

def is_newer(latest, current):
    try:
        return tuple(map(int, latest.split("."))) > tuple(map(int, current.split(".")))
    except Exception:
        return False

# =====================================================
# UPDATE FLOW (APP MODE ONLY)
# =====================================================
def perform_update(release):
    assets = release.get("assets", [])
    zip_asset = next((a for a in assets if a["name"].endswith(".zip")), None)

    if not zip_asset:
        messagebox.showerror("Update failed", "No update package found.")
        return

    tmp_zip = os.path.join(tempfile.gettempdir(), "LifeRPG_update.zip")
    urllib.request.urlretrieve(zip_asset["browser_download_url"], tmp_zip)

    with zipfile.ZipFile(tmp_zip, "r") as z:
        z.extractall(BASE_DIR)

    os.remove(tmp_zip)

    subprocess.Popen(
        [sys.executable],
        cwd=BASE_DIR,
        creationflags=subprocess.DETACHED_PROCESS
    )
    sys.exit(0)

# =====================================================
# INSTALLER GUI (ONLY FOR FIRST RUN)
# =====================================================
class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Life RPG Installer")
        self.geometry("560x340")
        self.install_dir = tk.StringVar()

        ttk.Label(
            self,
            text=f"Life RPG Installer (v{APP_VERSION})",
            font=("Segoe UI", 14)
        ).pack(pady=10)

        frame = ttk.Frame(self)
        frame.pack(pady=10)

        ttk.Entry(frame, textvariable=self.install_dir, width=50).pack(side="left", padx=5)
        ttk.Button(frame, text="Browse", command=self.browse).pack(side="left")

        ttk.Button(self, text="Install", command=self.install).pack(pady=20)

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)

    def install(self):
        base = self.install_dir.get()
        if not base:
            messagebox.showerror("Error", "Please choose a folder.")
            return

        os.makedirs(base, exist_ok=True)
        save_launcher_config({"install_path": base})

        with open(os.path.join(base, VERSION_FILE), "w") as f:
            f.write(APP_VERSION)

        self.destroy()
        subprocess.Popen(
            [sys.executable],
            cwd=base,
            creationflags=subprocess.DETACHED_PROCESS
        )
        sys.exit(0)

# =====================================================
# APP MODE (SAFE UPDATE CHECK)
# =====================================================
def run_app():
    try:
        release = get_latest_release()
        latest = release["tag_name"].lstrip("v")
        current = read_installed_version()

        if current and is_newer(latest, current):
            root = tk.Tk()
            root.withdraw()
            if messagebox.askyesno(
                "Update Available",
                f"Version {latest} is available.\n"
                f"You are running {current}.\n\n"
                "Download and install now?"
            ):
                perform_update(release)
    except Exception:
        pass  # Never block app launch

    from app_gui import LifeRPGApp
    LifeRPGApp().mainloop()

# =====================================================
# ENTRY POINT (FINAL, NON-REGRESSABLE)
# =====================================================
if __name__ == "__main__":
    if is_installed():
        run_app()
    else:
        Installer().mainloop()
