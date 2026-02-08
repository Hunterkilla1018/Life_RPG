import os
import json
import subprocess
import threading
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request

# ============================================================
# Identity
# ============================================================

APP_NAME = "Life RPG"
LAUNCHER_VERSION = "1.4"

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

GAME_EXE = "LifeRPG.exe"
LAUNCHER_EXE = "LifeRPG_Launcher.exe"

UPDATE_DIR = ".updates"
UPDATE_EXE = "LifeRPG_update.exe"
SWAP_SCRIPT = "apply_update.bat"
HASH_FILE = "hash.txt"

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.getcwd()), "LifeRPG")
CONFIG_FILE = os.path.join(CONFIG_DIR, "launcher.json")

# ============================================================
# Managed file: storage.py
# ============================================================

STORAGE_PY_CONTENT = """\
import os
import json

SAVE_DIR = "life_rpg_save"
PLAYER_FILE = os.path.join(SAVE_DIR, "player.json")

os.makedirs(SAVE_DIR, exist_ok=True)

def load_player():
    if not os.path.exists(PLAYER_FILE):
        return {"level": 1, "xp": 0}
    with open(PLAYER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_player(player):
    with open(PLAYER_FILE, "w", encoding="utf-8") as f:
        json.dump(player, f, indent=4)
"""

# ============================================================
# Helpers
# ============================================================

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "install_dir": "",
            "close_on_launch": True
        }
    return json.load(open(CONFIG_FILE, "r", encoding="utf-8"))

def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    json.dump(cfg, open(CONFIG_FILE, "w", encoding="utf-8"), indent=4)

def fetch_latest_release():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read().decode())

# ============================================================
# Launcher
# ============================================================

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} Launcher")
        self.geometry("780x520")
        self.resizable(False, False)

        self.config_data = load_config()
        self.install_dir = tk.StringVar(value=self.config_data.get("install_dir", ""))
        self.close_on_launch = tk.BooleanVar(value=self.config_data.get("close_on_launch", True))

        self.latest_release = None
        self.update_ready = False

        self.build_ui()
        self.after(100, self.check_updates)

    # --------------------------------------------------------

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x")

        ttk.Label(
            top,
            text=f"{APP_NAME} v{LAUNCHER_VERSION}",
            font=("Segoe UI", 14)
        ).pack(side="left", padx=10, pady=10)

        ttk.Button(top, text="⚙", command=self.open_settings).pack(side="right", padx=10)

        ttk.Entry(self, textvariable=self.install_dir, width=95).pack(pady=5)
        ttk.Button(self, text="Browse…", command=self.browse).pack()

        self.status = tk.StringVar(value="Idle")
        ttk.Label(self, textvariable=self.status).pack(pady=5)

        self.progress = ttk.Progressbar(self, length=740)
        self.progress.pack(pady=10)

        self.buttons = ttk.Frame(self)
        self.buttons.pack(pady=10)

        self.refresh_buttons()

    # --------------------------------------------------------

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)
            self.config_data["install_dir"] = path
            save_config(self.config_data)
            self.refresh_buttons()

    # --------------------------------------------------------

    def open_settings(self):
        win = tk.Toplevel(self)
        win.title("Settings")
        win.geometry("300x150")
        win.resizable(False, False)

        ttk.Checkbutton(
            win,
            text="Close launcher when game launches",
            variable=self.close_on_launch,
            command=self.save_settings
        ).pack(pady=20)

    def save_settings(self):
        self.config_data["close_on_launch"] = self.close_on_launch.get()
        save_config(self.config_data)

    # --------------------------------------------------------

    def refresh_buttons(self):
        for w in self.buttons.winfo_children():
            w.destroy()

        base = self.install_dir.get()
        game = os.path.join(base, GAME_EXE)

        if not base or not os.path.exists(game):
            ttk.Button(self.buttons, text="Install", command=self.install).pack()
            return

        ttk.Button(self.buttons, text="Launch", command=self.launch).pack(side="left", padx=5)
        ttk.Button(self.buttons, text="Repair", command=self.repair).pack(side="left", padx=5)

        if self.update_ready:
            ttk.Button(self.buttons, text="Apply Update", command=self.apply_update_prompt).pack(side="left", padx=5)

    # --------------------------------------------------------

    def check_updates(self):
        self.latest_release = fetch_latest_release()
        base = self.install_dir.get()
        game = os.path.join(base, GAME_EXE)

        if not os.path.exists(game):
            return

        asset = next(a for a in self.latest_release["assets"] if a["name"] == GAME_EXE)
        expected_hash = asset.get("label")

        if expected_hash:
            current = sha256(game)
            if current != expected_hash:
                self.status.set("Integrity check failed — repairing")
                self.repair()
                return

        threading.Thread(target=self.download_update, daemon=True).start()

    # --------------------------------------------------------

    def download_update(self):
        asset = next(a for a in self.latest_release["assets"] if a["name"] == GAME_EXE)
        url = asset["browser_download_url"]

        base = self.install_dir.get()
        updates = os.path.join(base, UPDATE_DIR)
        os.makedirs(updates, exist_ok=True)

        dest = os.path.join(updates, UPDATE_EXE)
        with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
            f.write(r.read())

        self.update_ready = True
        self.status.set("Update downloaded")
        self.refresh_buttons()

    # --------------------------------------------------------

    def apply_update_prompt(self):
        if messagebox.askyesno("Update Ready", "Apply update now?"):
            self.apply_update()

    def apply_update(self):
        base = self.install_dir.get()
        updates = os.path.join(base, UPDATE_DIR)

        script = os.path.join(updates, SWAP_SCRIPT)
        with open(script, "w") as f:
            f.write(f"""@echo off
timeout /t 2 >nul
move "{os.path.join(updates, UPDATE_EXE)}" "{os.path.join(base, GAME_EXE)}"
start "" "{os.path.join(base, GAME_EXE)}"
""")

        subprocess.Popen(["cmd", "/c", script])
        if self.close_on_launch.get():
            self.destroy()

    # --------------------------------------------------------

    def install(self):
        self.download_update()
        self.apply_update()

    def repair(self):
        self.download_update()

    def launch(self):
        subprocess.Popen([os.path.join(self.install_dir.get(), GAME_EXE)])
        if self.close_on_launch.get():
            self.destroy()


# ============================================================
# Entry
# ============================================================

if __name__ == "__main__":
    Launcher().mainloop()
