import os
import json
import hashlib
import urllib.request
import subprocess
import threading
import time
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog

# ============================================================
# Identity
# ============================================================

APP_NAME = "Life RPG"
LAUNCHER_VERSION = "1.5.0-alpha2"

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

GAME_EXE = "LifeRPG.exe"
FULL_INSTALL_ZIP = "LifeRPG_full.zip"
MANIFEST_NAME = "manifest.json"

# ============================================================
# Paths
# ============================================================

APPDATA = os.path.join(os.environ["APPDATA"], "LifeRPG")
RUNTIME = os.path.join(APPDATA, "runtime")
CONFIG_FILE = os.path.join(APPDATA, "launcher.json")
MANIFEST_PATH = os.path.join(RUNTIME, MANIFEST_NAME)
UPDATE_EXE = os.path.join(RUNTIME, "LifeRPG_update.exe")
ZIP_PATH = os.path.join(RUNTIME, FULL_INSTALL_ZIP)
SWAP_SCRIPT = os.path.join(RUNTIME, "apply_update.bat")

os.makedirs(RUNTIME, exist_ok=True)

# ============================================================
# Helpers
# ============================================================

def normalize_version(v):
    return v.lstrip("v").strip() if v else ""

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
    except:
        return False

def load_config():
    defaults = {
        "install_dir": "",
        "installed_version": "",
        "close_on_launch": True
    }
    if not os.path.exists(CONFIG_FILE):
        return defaults.copy()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for k, v in defaults.items():
        data.setdefault(k, v)
    save_config(data)
    return data

def save_config(cfg):
    os.makedirs(APPDATA, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

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
        self.title("LIFE RPG :: SYSTEM INTERFACE")
        self.geometry("900x600")
        self.configure(bg="#0b0f14")
        self.resizable(False, False)

        self.cfg = load_config()
        self.install_dir = tk.StringVar(value=self.cfg["install_dir"])

        self.latest_release = None
        self.manifest = None

        self.sys_status = tk.StringVar(value="INITIALIZING")
        self.net_status = tk.StringVar(value="UNKNOWN")
        self.integrity_status = tk.StringVar(value="UNKNOWN")
        self.update_status = tk.StringVar(value="UNKNOWN")

        self._build_ui()
        self.after(100, self.startup_async)

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):
        header = tk.Frame(self, bg="#0b0f14")
        header.pack(fill="x", padx=15, pady=10)

        tk.Label(
            header,
            text=f"LIFE RPG :: SYSTEM INTERFACE   v{LAUNCHER_VERSION}",
            fg="#7ddcff",
            bg="#0b0f14",
            font=("Consolas", 14, "bold")
        ).pack(anchor="w")

        self.status_label = tk.Label(
            self,
            fg="#b6f0ff",
            bg="#0b0f14",
            font=("Consolas", 10),
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=15)

        self.actions = ttk.Frame(self)
        self.actions.pack(pady=40)

        footer = ttk.Frame(self)
        footer.pack(side="bottom", pady=10)
        ttk.Entry(footer, textvariable=self.install_dir, width=100).pack()
        ttk.Button(footer, text="Browse…", command=self.browse).pack(pady=5)

        self._refresh_status()

    def _refresh_status(self):
        self.status_label.config(
            text=f"SYSTEM: {self.sys_status.get()} | NET: {self.net_status.get()} | "
                 f"INTEGRITY: {self.integrity_status.get()} | UPDATE: {self.update_status.get()}"
        )

    def clear_actions(self):
        for w in self.actions.winfo_children():
            w.destroy()

    # ========================================================
    # Startup Logic
    # ========================================================

    def startup_async(self):
        threading.Thread(target=self.startup_logic, daemon=True).start()

    def startup_logic(self):
        self.net_status.set("OK" if internet_available() else "OFFLINE")
        self._refresh_status()

        if self.net_status.get() == "OFFLINE":
            self.apply_state("NO_INTERNET")
            return

        self.latest_release = fetch_latest_release()
        latest = normalize_version(self.latest_release["tag_name"])
        installed = normalize_version(self.cfg["installed_version"])

        base = self.install_dir.get()
        game = os.path.join(base, GAME_EXE)

        if not base or not os.path.exists(base):
            self.apply_state("NOT_INSTALLED")
            return

        if not installed or installed != latest:
            self.apply_state("UPDATE_REQUIRED")
            return

        self.download_manifest()
        if not self.manifest:
            self.apply_state("MANIFEST_MISSING")
            return

        if not self.verify_all_files(base):
            self.apply_state("INTEGRITY_FAILED")
            return

        self.apply_state("READY")

    # ========================================================
    # State Handling
    # ========================================================

    def apply_state(self, state):
        self.clear_actions()
        self.sys_status.set("READY" if state == "READY" else "BLOCKED")

        states = {
            "NO_INTERNET": ("OFFLINE", "UNKNOWN"),
            "NOT_INSTALLED": ("INSTALL REQUIRED", "UNKNOWN"),
            "UPDATE_REQUIRED": ("UPDATE REQUIRED", "UNKNOWN"),
            "MANIFEST_MISSING": ("MANIFEST MISSING", "UNKNOWN"),
            "INTEGRITY_FAILED": ("REPAIR REQUIRED", "FAILED"),
            "READY": ("NONE", "VERIFIED")
        }

        self.update_status.set(states[state][0])
        self.integrity_status.set(states[state][1])

        if state == "READY":
            ttk.Button(self.actions, text="LAUNCH SYSTEM", command=self.launch).pack()
        elif state == "NOT_INSTALLED":
            ttk.Button(self.actions, text="INSTALL SYSTEM", command=self.install).pack()
        elif state == "INTEGRITY_FAILED":
            ttk.Button(self.actions, text="REPAIR SYSTEM", command=self.install).pack()
        else:
            ttk.Button(self.actions, text="DOWNLOAD UPDATE", command=self.download_update).pack()

        self._refresh_status()

    # ========================================================
    # Manifest & Integrity
    # ========================================================

    def download_manifest(self):
        asset = next(
            (a for a in self.latest_release["assets"] if a["name"] == MANIFEST_NAME),
            None
        )
        if not asset:
            self.manifest = None
            return

        download(asset["browser_download_url"], MANIFEST_PATH)
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def verify_all_files(self, base_dir):
        for rel_path, expected_hash in self.manifest.get("files", {}).items():
            full_path = os.path.join(base_dir, rel_path)
            if not os.path.exists(full_path):
                return False
            if sha256(full_path) != expected_hash:
                return False
        return True

    # ========================================================
    # Actions
    # ========================================================

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)
            self.cfg["install_dir"] = path
            save_config(self.cfg)
            self.startup_async()

    def install(self):
        self.clear_actions()
        self.update_status.set("INSTALLING")
        self._refresh_status()

        def run():
            asset = next(
                (a for a in self.latest_release["assets"] if a["name"] == FULL_INSTALL_ZIP),
                None
            )
            if not asset:
                self.apply_state("UPDATE_REQUIRED")
                return

            download(asset["browser_download_url"], ZIP_PATH)

            try:
                with zipfile.ZipFile(ZIP_PATH, "r") as z:
                    z.extractall(self.install_dir.get())
            except:
                self.apply_state("UPDATE_REQUIRED")
                return

            self.cfg["installed_version"] = normalize_version(
                self.latest_release["tag_name"]
            )
            save_config(self.cfg)
            self.startup_async()

        threading.Thread(target=run, daemon=True).start()

    def download_update(self):
        self.clear_actions()
        self.update_status.set("DOWNLOADING")
        self._refresh_status()

        def run():
            asset = next(
                (a for a in self.latest_release["assets"] if a["name"] == GAME_EXE),
                None
            )
            if not asset:
                self.apply_state("UPDATE_REQUIRED")
                return

            download(asset["browser_download_url"], UPDATE_EXE)
            self.apply_update()

        threading.Thread(target=run, daemon=True).start()

    def apply_update(self):
        with open(SWAP_SCRIPT, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
timeout /t 2 >nul
move "{UPDATE_EXE}" "{os.path.join(self.install_dir.get(), GAME_EXE)}"
""")

        subprocess.call(["cmd", "/c", SWAP_SCRIPT])
        time.sleep(1)
        self.startup_async()

    def launch(self):
        subprocess.Popen([os.path.join(self.install_dir.get(), GAME_EXE)])
        if self.cfg["close_on_launch"]:
            self.destroy()

# ============================================================
# Entry
# ============================================================

if __name__ == "__main__":
    Launcher().mainloop()
