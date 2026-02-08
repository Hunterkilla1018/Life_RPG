import os
import json
import hashlib
import urllib.request
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ============================================================
# Identity
# ============================================================

APP_NAME = "Life RPG"
LAUNCHER_VERSION = "1.4.6"

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

GAME_EXE = "LifeRPG.exe"
MANIFEST_NAME = "manifest.json"

# ============================================================
# Paths
# ============================================================

APPDATA = os.path.join(os.environ["APPDATA"], "LifeRPG")
RUNTIME = os.path.join(APPDATA, "runtime")
CONFIG_FILE = os.path.join(APPDATA, "launcher.json")
MANIFEST_PATH = os.path.join(RUNTIME, MANIFEST_NAME)
UPDATE_EXE = os.path.join(RUNTIME, "LifeRPG_update.exe")
SWAP_SCRIPT = os.path.join(RUNTIME, "apply_update.bat")

os.makedirs(RUNTIME, exist_ok=True)

# ============================================================
# Helpers
# ============================================================

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def internet_available():
    try:
        urllib.request.urlopen("https://api.github.com", timeout=5)
        return True
    except Exception:
        return False

def load_config():
    defaults = {
        "install_dir": "",
        "installed_version": "",
        "close_on_launch": True,
        "minimize_on_launch": False,
        "update_interval_min": 1
    }

    if not os.path.exists(CONFIG_FILE):
        return defaults.copy()

    data = json.load(open(CONFIG_FILE, "r", encoding="utf-8"))
    for k, v in defaults.items():
        data.setdefault(k, v)
    save_config(data)
    return data

def save_config(cfg):
    os.makedirs(APPDATA, exist_ok=True)
    json.dump(cfg, open(CONFIG_FILE, "w", encoding="utf-8"), indent=4)

def fetch_latest_release():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode())

def download(url, dest):
    with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
        f.write(r.read())

# ============================================================
# Launcher
# ============================================================

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} Launcher")
        self.geometry("820x580")
        self.resizable(False, False)

        self.cfg = load_config()
        self.install_dir = tk.StringVar(value=self.cfg["install_dir"])

        self.latest_release = None
        self.manifest = None
        self.integrity_ok = False
        self.update_ready = False
        self.game_running = False

        self.status = tk.StringVar(value="Starting…")

        self.build_ui()
        threading.Thread(target=self.startup_check, daemon=True).start()

    # --------------------------------------------------------

    def build_ui(self):
        ttk.Label(self, text=f"{APP_NAME} v{LAUNCHER_VERSION}",
                  font=("Segoe UI", 14)).pack(pady=10)

        ttk.Entry(self, textvariable=self.install_dir, width=100).pack()
        ttk.Button(self, text="Browse…", command=self.browse).pack(pady=5)

        ttk.Label(self, textvariable=self.status).pack(pady=10)

        self.buttons = ttk.Frame(self)
        self.buttons.pack(pady=20)

        ttk.Button(self, text="Check now", command=self.manual_check).pack()

    # --------------------------------------------------------

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)
            self.cfg["install_dir"] = path
            save_config(self.cfg)
            self.startup_check()

    # --------------------------------------------------------
    # Startup logic (STRICT)
    # --------------------------------------------------------

    def startup_check(self):
        self.clear_buttons()

        if not internet_available():
            self.status.set("No internet connection — launch blocked")
            return

        base = self.install_dir.get()
        game = os.path.join(base, GAME_EXE)

        if not base or not os.path.exists(game):
            self.status.set("Game not installed")
            ttk.Button(self.buttons, text="Install", command=self.install).pack()
            return

        self.latest_release = fetch_latest_release()
        latest_version = self.latest_release["tag_name"]

        if self.cfg["installed_version"] != latest_version:
            self.status.set("Update required — launch blocked")
            ttk.Button(self.buttons, text="Download Update", command=self.download_update).pack()
            return

        self.download_manifest()
        if not self.verify_integrity(game):
            self.status.set("Integrity check failed — repair required")
            ttk.Button(self.buttons, text="Repair", command=self.repair).pack()
            return

        self.status.set("Ready")
        ttk.Button(self.buttons, text="Launch", command=self.launch).pack()

    # --------------------------------------------------------

    def clear_buttons(self):
        for w in self.buttons.winfo_children():
            w.destroy()

    # --------------------------------------------------------
    # Manifest & Integrity
    # --------------------------------------------------------

    def download_manifest(self):
        asset = next(a for a in self.latest_release["assets"] if a["name"] == MANIFEST_NAME)
        download(asset["browser_download_url"], MANIFEST_PATH)
        self.manifest = json.load(open(MANIFEST_PATH, "r", encoding="utf-8"))

    def verify_integrity(self, game_path):
        expected = self.manifest["files"].get(GAME_EXE)
        if not expected:
            return False
        return sha256(game_path) == expected

    # --------------------------------------------------------
    # Updates
    # --------------------------------------------------------

    def download_update(self):
        self.status.set("Downloading update…")
        asset = next(a for a in self.latest_release["assets"] if a["name"] == GAME_EXE)
        download(asset["browser_download_url"], UPDATE_EXE)
        self.update_ready = True
        self.status.set("Update ready — apply required")
        self.clear_buttons()
        ttk.Button(self.buttons, text="Apply Update", command=self.apply_update).pack()

    def apply_update(self):
        game = os.path.join(self.install_dir.get(), GAME_EXE)

        with open(SWAP_SCRIPT, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
timeout /t 2 >nul
move "{UPDATE_EXE}" "{game}"
start "" "{game}"
""")

        self.cfg["installed_version"] = self.latest_release["tag_name"]
        save_config(self.cfg)

        subprocess.Popen(["cmd", "/c", SWAP_SCRIPT])
        self.destroy()

    def install(self):
        self.download_update()

    def repair(self):
        self.download_update()

    # --------------------------------------------------------

    def manual_check(self):
        threading.Thread(target=self.startup_check, daemon=True).start()

    def launch(self):
        subprocess.Popen([os.path.join(self.install_dir.get(), GAME_EXE)])
        if self.cfg["close_on_launch"]:
            self.destroy()

# ============================================================
# Entry
# ============================================================

if __name__ == "__main__":
    Launcher().mainloop()
