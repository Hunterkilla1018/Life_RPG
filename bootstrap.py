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
# PATHS
# =====================================================
APPDATA_DIR = os.path.join(os.getenv("APPDATA"), "LifeRPG")
LAUNCHER_CONFIG = os.path.join(APPDATA_DIR, "launcher.json")
BASE_DIR = os.path.dirname(sys.executable)

# =====================================================
# FILES TO INSTALL
# =====================================================
FILES = {
    "config.py": """APP_NAME = "Life RPG"
SAVE_DIR = "life_rpg_save"
""",
    "storage.py": """import os, json
from config import SAVE_DIR

os.makedirs(SAVE_DIR, exist_ok=True)
PLAYER_FILE = os.path.join(SAVE_DIR, "player.json")

def load_player():
    if not os.path.exists(PLAYER_FILE):
        return {"level": 1, "xp": 0}
    return json.load(open(PLAYER_FILE))

def save_player(p):
    json.dump(p, open(PLAYER_FILE, "w"), indent=4)
""",
    "app_gui.py": """import tkinter as tk
from tkinter import ttk
from storage import load_player

class LifeRPGApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Life RPG")
        self.geometry("500x300")
        p = load_player()
        ttk.Label(self, text="Life RPG", font=("Segoe UI", 14)).pack(pady=20)
        ttk.Label(self, text=f"Level: {p['level']}  XP: {p['xp']}").pack()
""",
    "main.py": """from app_gui import LifeRPGApp
LifeRPGApp().mainloop()
""",
    VERSION_FILE: APP_VERSION
}

# =====================================================
# HELPERS
# =====================================================
def ensure_appdata():
    os.makedirs(APPDATA_DIR, exist_ok=True)

def is_installed():
    return os.path.exists(LAUNCHER_CONFIG)

def save_launcher_config(data):
    ensure_appdata()
    with open(LAUNCHER_CONFIG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

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
        data = json.loads(r.read().decode())
        return data

def is_newer(latest, current):
    return tuple(map(int, latest.split("."))) > tuple(map(int, current.split(".")))

# =====================================================
# UPDATE FLOW
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
# INSTALLER GUI (unchanged)
# =====================================================
class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Life RPG Installer")
        self.geometry("560x340")
        self.install_dir = tk.StringVar()

        ttk.Label(self, text=f"Life RPG Installer (v{APP_VERSION})",
                  font=("Segoe UI", 14)).pack(pady=10)

        frame = ttk.Frame(self)
        frame.pack()

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
            return

        os.makedirs(base, exist_ok=True)
        save_launcher_config({"install_path": base})

        for name, content in FILES.items():
            with open(os.path.join(base, name), "w", encoding="utf-8") as f:
                f.write(content)

        self.destroy()
        subprocess.Popen([sys.executable], cwd=base)
        sys.exit(0)

# =====================================================
# APP MODE
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
# ENTRY POINT
# =====================================================
if __name__ == "__main__":
    if is_installed():
        run_app()
    else:
        Installer().mainloop()
