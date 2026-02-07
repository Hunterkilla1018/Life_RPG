import os
import sys
import time
import json
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# =====================================================
# VERSIONING (SINGLE SOURCE OF TRUTH)
# =====================================================
APP_NAME = "LifeRPG"
APP_VERSION = "1.1.4"
VERSION_FILE = "version.txt"

# =====================================================
# MODE SELECTION
# =====================================================
RUN_INSTALLER = "--install" in sys.argv

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

    "game_logic.py": """def apply(player, tasks):
    for _ in tasks:
        player["xp"] += 10
    return player
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
# HELPER FUNCTIONS
# =====================================================
def read_installed_version(path):
    try:
        with open(os.path.join(path, VERSION_FILE), "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


def get_app_executable_path():
    """
    Returns the path to LifeRPG.exe when running from a PyInstaller onedir build.
    """
    base_dir = os.path.dirname(sys.executable)
    return os.path.join(base_dir, f"{APP_NAME}.exe")


# =====================================================
# INSTALLER GUI
# =====================================================
class Installer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Life RPG Installer")
        self.geometry("560x330")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.install_dir = tk.StringVar()
        self.status = tk.StringVar(value="Choose an installation folder")

        ttk.Label(
            self,
            text=f"Life RPG Installer (v{APP_VERSION})",
            font=("Segoe UI", 14)
        ).pack(pady=10)

        path_frame = ttk.Frame(self)
        path_frame.pack(pady=5)

        ttk.Entry(
            path_frame,
            textvariable=self.install_dir,
            width=50
        ).pack(side="left", padx=5)

        ttk.Button(
            path_frame,
            text="Browse",
            command=self.browse
        ).pack(side="left")

        self.progress = ttk.Progressbar(self, length=500)
        self.progress.pack(pady=15)

        ttk.Label(self, textvariable=self.status, wraplength=520).pack(pady=5)

        ttk.Button(
            self,
            text="Install",
            command=self.install
        ).pack(pady=10)

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)

    def install(self):
        base = self.install_dir.get()

        if not base:
            messagebox.showerror("Error", "Please choose an installation folder.")
            return

        os.makedirs(base, exist_ok=True)
        os.makedirs(os.path.join(base, "life_rpg_save"), exist_ok=True)

        installed_version = read_installed_version(base)

        if installed_version:
            self.status.set(
                f"Updating existing install (v{installed_version} → v{APP_VERSION})"
            )
        else:
            self.status.set("Performing fresh install")

        self.update_idletasks()
        time.sleep(0.4)

        self.progress["maximum"] = len(FILES)
        step = 0

        for name, content in FILES.items():
            self.status.set(f"Installing {name}...")
            self.update_idletasks()

            with open(os.path.join(base, name), "w", encoding="utf-8") as f:
                f.write(content)

            time.sleep(0.12)
            step += 1
            self.progress["value"] = step

        self.status.set("Launching Life RPG...")
        self.update_idletasks()
        time.sleep(0.4)

        # =================================================
        # LAUNCH APP MODE AND EXIT INSTALLER CLEANLY
        # =================================================
        app_exe = get_app_executable_path()

        self.destroy()

        subprocess.Popen(
            [app_exe],
            cwd=os.path.dirname(app_exe),
            creationflags=subprocess.DETACHED_PROCESS
        )

        sys.exit(0)


# =====================================================
# APP MODE (NORMAL RUN)
# =====================================================
def run_app():
    from app_gui import LifeRPGApp
    app = LifeRPGApp()
    app.mainloop()


# =====================================================
# ENTRY POINT
# =====================================================
if __name__ == "__main__":
    if RUN_INSTALLER:
        Installer().mainloop()
    else:
        run_app()
