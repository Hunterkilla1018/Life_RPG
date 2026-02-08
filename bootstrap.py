import os
import json
import hashlib
import urllib.request
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog

# ============================================================
# Identity
# ============================================================

APP_NAME = "Life RPG"
LAUNCHER_VERSION = "1.4.7-hotfix1"

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
# Theme + Labels (RPG PREP)
# ============================================================

THEME = {
    "bg": "#1e1e1e",
    "fg": "#e6e6e6",
    "accent": "#c9a24d",
    "danger": "#c94d4d",
    "success": "#4dc97a"
}

LABELS = {
    "starting": "Starting…",
    "ready": "Ready",
    "checking": "Checking for updates…",
    "update_required": "Update required — launch blocked",
    "integrity_failed": "Integrity check failed — repair required",
    "no_internet": "No internet connection — launch blocked",
    "not_installed": "Game not installed"
}

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

        self.status = tk.StringVar(value=LABELS["starting"])

        self._build_styles()
        self._build_layout()

        # ✅ run startup logic safely
        self.after(50, self.startup_check_async)

    # --------------------------------------------------------
    # Styles
    # --------------------------------------------------------

    def _build_styles(self):
        style = ttk.Style()
        style.configure("Primary.TButton")
        style.configure("Secondary.TButton")
        style.configure("Danger.TButton")

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    def _build_layout(self):
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill="x", pady=10)

        ttk.Label(
            self.header_frame,
            text=f"{APP_NAME} v{LAUNCHER_VERSION}",
            font=("Segoe UI", 14)
        ).pack()

        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill="x", pady=10)

        ttk.Label(self.status_frame, textvariable=self.status).pack()

        self.primary_action_frame = ttk.Frame(self)
        self.primary_action_frame.pack(pady=15)

        self.secondary_action_frame = ttk.Frame(self)
        self.secondary_action_frame.pack(pady=5)

        self.footer_frame = ttk.Frame(self)
        self.footer_frame.pack(side="bottom", pady=10)

        ttk.Entry(self.footer_frame, textvariable=self.install_dir, width=100).pack()
        ttk.Button(self.footer_frame, text="Browse…", command=self.browse).pack(pady=5)

    # --------------------------------------------------------

    def clear_actions(self):
        for frame in (self.primary_action_frame, self.secondary_action_frame):
            for w in frame.winfo_children():
                w.destroy()

    # --------------------------------------------------------
    # Startup logic (FIXED)
    # --------------------------------------------------------

    def startup_check_async(self):
        threading.Thread(target=self._startup_logic, daemon=True).start()

    def _startup_logic(self):
        result = {}

        if not internet_available():
            result["state"] = "no_internet"
        else:
            base = self.install_dir.get()
            game = os.path.join(base, GAME_EXE)

            if not base or not os.path.exists(game):
                result["state"] = "not_installed"
            else:
                self.latest_release = fetch_latest_release()
                latest_version = self.latest_release["tag_name"]

                if self.cfg["installed_version"] != latest_version:
                    result["state"] = "update_required"
                else:
                    self.download_manifest()
                    if not self.verify_integrity(game):
                        result["state"] = "integrity_failed"
                    else:
                        result["state"] = "ready"

        # marshal UI update back to main thread
        self.after(0, lambda: self.apply_startup_result(result))

    def apply_startup_result(self, result):
        self.clear_actions()

        state = result["state"]

        if state == "no_internet":
            self.status.set(LABELS["no_internet"])
        elif state == "not_installed":
            self.status.set(LABELS["not_installed"])
            ttk.Button(self.primary_action_frame, text="Install",
                       style="Primary.TButton", command=self.install).pack()
        elif state == "update_required":
            self.status.set(LABELS["update_required"])
            ttk.Button(self.primary_action_frame, text="Download Update",
                       style="Primary.TButton", command=self.download_update).pack()
        elif state == "integrity_failed":
            self.status.set(LABELS["integrity_failed"])
            ttk.Button(self.primary_action_frame, text="Repair",
                       style="Danger.TButton", command=self.repair).pack()
        elif state == "ready":
            self.status.set(LABELS["ready"])
            ttk.Button(self.primary_action_frame, text="Launch",
                       style="Primary.TButton", command=self.launch).pack()

    # --------------------------------------------------------

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)
            self.cfg["install_dir"] = path
            save_config(self.cfg)
            self.startup_check_async()

    # --------------------------------------------------------

    def download_manifest(self):
        asset = next(a for a in self.latest_release["assets"] if a["name"] == MANIFEST_NAME)
        download(asset["browser_download_url"], MANIFEST_PATH)
        self.manifest = json.load(open(MANIFEST_PATH, "r", encoding="utf-8"))

    def verify_integrity(self, game_path):
        expected = self.manifest["files"].get(GAME_EXE)
        return expected and sha256(game_path) == expected

    # --------------------------------------------------------

    def download_update(self):
        self.status.set("Downloading update…")
        asset = next(a for a in self.latest_release["assets"] if a["name"] == GAME_EXE)
        download(asset["browser_download_url"], UPDATE_EXE)

        self.clear_actions()
        ttk.Button(self.primary_action_frame, text="Apply Update",
                   style="Primary.TButton", command=self.apply_update).pack()

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

    def launch(self):
        subprocess.Popen([os.path.join(self.install_dir.get(), GAME_EXE)])
        if self.cfg["close_on_launch"]:
            self.destroy()

# ============================================================
# Entry
# ============================================================

if __name__ == "__main__":
    Launcher().mainloop()
