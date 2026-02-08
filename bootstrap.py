import os
import sys
import time
import json
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request

# =====================================================
# VERSIONING
# =====================================================
APP_NAME = "LifeRPG"
APP_VERSION = "1.1.6"
VERSION_FILE = "version.txt"

GITHUB_REPO = "Hunterkilla1018/Life_RPG"

# =====================================================
# PATHS
# =====================================================
APPDATA_DIR = os.path.join(os.getenv("APPDATA"), "LifeRPG")
LAUNCHER_CONFIG = os.path.join(APPDATA_DIR, "launcher.json")

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

def load_launcher_config():
    try:
        with open(LAUNCHER_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_launcher_config(data):
    ensure_appdata()
    with open(LAUNCHER_CONFIG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_app_executable():
    return os.path.join(os.path.dirname(sys.executable), f"{APP_NAME}.exe")

# =====================================================
# INSTALLER GUI
# =====================================================
class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Life RPG Installer")
        self.geometry("560x340")
        self.resizable(False, False)
        self.install_dir = tk.StringVar()
        self.status = tk.StringVar(value="Choose an installation folder")

        ttk.Label(self, text=f"Life RPG Installer (v{APP_VERSION})",
                  font=("Segoe UI", 14)).pack(pady=10)

        frame = ttk.Frame(self)
        frame.pack(pady=5)

        ttk.Entry(frame, textvariable=self.install_dir, width=50).pack(side="left", padx=5)
        ttk.Button(frame, text="Browse", command=self.browse).pack(side="left")

        self.progress = ttk.Progressbar(self, length=500)
        self.progress.pack(pady=15)

        ttk.Label(self, textvariable=self.status, wraplength=520).pack()

        ttk.Button(self, text="Install", command=self.install).pack(pady=10)

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)

    def install(self):
        base = self.install_dir.get()
        if not base:
            messagebox.showerror("Error", "Choose a folder.")
            return

        os.makedirs(base, exist_ok=True)
        save_launcher_config({"install_path": base})

        self.progress["maximum"] = len(FILES)
        for i, (name, content) in enumerate(FILES.items(), 1):
            self.status.set(f"Installing {name}")
            self.update_idletasks()
            with open(os.path.join(base, name), "w", encoding="utf-8") as f:
                f.write(content)
            self.progress["value"] = i
            time.sleep(0.1)

        self.destroy()
        subprocess.Popen(
            [get_app_executable()],
            creationflags=subprocess.DETACHED_PROCESS
        )
        sys.exit(0)

# =====================================================
# APP MODE
# =====================================================
def run_app():
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
