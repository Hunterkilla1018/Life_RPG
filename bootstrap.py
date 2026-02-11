print("BOOTSTRAP FILE PATH:", __file__)

import os
import json
import hashlib
import urllib.request
import subprocess
import threading
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime

# =========================
# VERSION / IDENTITY
# =========================

LAUNCHER_VERSION = "1.5.0-alpha11"

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

GAME_EXE = "LifeRPG.exe"
FULL_INSTALL_ZIP = "LifeRPG_full.zip"
MANIFEST_NAME = "manifest.json"

# =========================
# PATHS
# =========================

APPDATA = os.path.join(os.environ.get("APPDATA", os.getcwd()), "LifeRPG")
RUNTIME = os.path.join(APPDATA, "runtime")
CONFIG_FILE = os.path.join(APPDATA, "launcher.json")

RUNTIME_MANIFEST = os.path.join(RUNTIME, MANIFEST_NAME)
ZIP_PATH = os.path.join(RUNTIME, FULL_INSTALL_ZIP)

GAME_SAVE_DIR_NAME = "life_rpg_save"

os.makedirs(RUNTIME, exist_ok=True)

# =========================
# HELPERS
# =========================

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
    except Exception:
        return False

def load_config():
    cfg = {
        "install_dir": "",
        "installed_version": "",
        "close_on_launch": True
    }

    os.makedirs(APPDATA, exist_ok=True)

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass  # corrupted config → regenerate

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

    return cfg

print("load_config defined:", "load_config" in globals())

def fetch_latest_release():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode())

def download(url, dest):
    urllib.request.urlretrieve(url, dest)

# =========================
# LAUNCHER
# =========================

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Life RPG :: Launcher")
        self.geometry("900x650")
        self.configure(bg="#0b0f14")

        # 🔑 DO NOT return from __init__
        self.cfg = load_config()
        self.install_dir = tk.StringVar(value=self.cfg["install_dir"])

        self.latest_release = None
        self.manifest = None
        self.frozen = False

        self.sys = tk.StringVar(value="INIT")
        self.net = tk.StringVar(value="UNKNOWN")
        self.integrity = tk.StringVar(value="UNKNOWN")
        self.update = tk.StringVar(value="UNKNOWN")

        self._ui()
        self.after(100, self.startup_async)

    # ---------- LOGGING ----------

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.console.insert("end", f"[{ts}] {msg}\n")
        self.console.see("end")

    # ---------- UI ----------

    def _ui(self):
        tk.Label(
            self,
            text=f"Life RPG Launcher  v{LAUNCHER_VERSION}",
            fg="#7ddcff",
            bg="#0b0f14",
            font=("Consolas", 14, "bold")
        ).pack(anchor="w", padx=15, pady=10)

        self.status = tk.Label(self, fg="#b6f0ff", bg="#0b0f14", font=("Consolas", 10))
        self.status.pack(fill="x", padx=15)

        self.actions = ttk.Frame(self)
        self.actions.pack(pady=10)

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x", padx=15)

        self.console = tk.Text(self, bg="#05070a", fg="#b6f0ff", font=("Consolas", 9))
        self.console.pack(fill="both", expand=True, padx=15, pady=10)

        footer = ttk.Frame(self)
        footer.pack(pady=5)

        ttk.Entry(footer, textvariable=self.install_dir, width=80).pack(side="left")
        ttk.Button(footer, text="Browse", command=self.browse).pack(side="left")

        self.refresh_status()

    def refresh_status(self):
        self.status.config(
            text=f"SYSTEM: {self.sys.get()} | NET: {self.net.get()} | "
                 f"INTEGRITY: {self.integrity.get()} | UPDATE: {self.update.get()}"
        )

    def clear_actions(self):
        for w in self.actions.winfo_children():
            w.destroy()

    # ---------- STARTUP ----------

    def startup_async(self):
        if not self.frozen:
            threading.Thread(target=self.startup_logic, daemon=True).start()

    def startup_logic(self):
        self.log("Startup")

        self.net.set("OK" if internet_available() else "OFFLINE")
        self.refresh_status()

        if self.net.get() == "OFFLINE":
            self.state("NO_INTERNET")
            return

        self.latest_release = fetch_latest_release()
        latest = normalize_version(self.latest_release["tag_name"])
        installed = normalize_version(self.cfg["installed_version"])

        self.log(f"Latest: {latest} | Installed: {installed or 'none'}")

        base = self.install_dir.get()
        if not base or not os.path.exists(base):
            self.state("NOT_INSTALLED")
            return

        self.ensure_game_save_dir(base)

        if installed != latest:
            self.state("UPDATE_REQUIRED")
            return

        if not self.load_manifest():
            self.state("MANIFEST_MISSING")
            return

        if not self.verify_all(base):
            self.state("INTEGRITY_FAILED")
            return

        self.state("READY")

    # ---------- STATES ----------

    def state(self, s):
        self.clear_actions()
        self.sys.set("READY" if s == "READY" else "BLOCKED")

        mapping = {
            "NO_INTERNET": ("OFFLINE", "UNKNOWN"),
            "NOT_INSTALLED": ("INSTALL REQUIRED", "UNKNOWN"),
            "UPDATE_REQUIRED": ("UPDATE REQUIRED", "UNKNOWN"),
            "MANIFEST_MISSING": ("MANIFEST MISSING", "UNKNOWN"),
            "INTEGRITY_FAILED": ("REPAIR REQUIRED", "FAILED"),
            "READY": ("NONE", "VERIFIED")
        }

        self.update.set(mapping[s][0])
        self.integrity.set(mapping[s][1])

        if s == "READY":
            ttk.Button(self.actions, text="LAUNCH", command=self.launch).pack()
        elif s in ("NOT_INSTALLED", "INTEGRITY_FAILED"):
            ttk.Button(self.actions, text="INSTALL / REPAIR", command=self.install).pack()
        else:
            ttk.Button(self.actions, text="UPDATE", command=self.install).pack()

        self.refresh_status()

    # ---------- MANIFEST ----------

    def load_manifest(self):
        asset = next(
            (a for a in self.latest_release["assets"] if a["name"] == MANIFEST_NAME),
            None
        )
        if not asset:
            self.log("ERROR: manifest.json missing from release")
            return False

        download(asset["browser_download_url"], RUNTIME_MANIFEST)

        with open(RUNTIME_MANIFEST, "r", encoding="utf-8-sig") as f:
            self.manifest = json.load(f)

        with open(os.path.join(self.install_dir.get(), MANIFEST_NAME), "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=4)

        self.log("Manifest loaded")
        return True

    def verify_all(self, base):
        for rel, expected in self.manifest["files"].items():
            fp = os.path.join(base, rel)
            if not os.path.exists(fp):
                self.log(f"VERIFY FAIL: missing {rel}")
                return False
            if sha256(fp) != expected:
                self.log(f"VERIFY FAIL: hash mismatch {rel}")
                return False
        self.log("Integrity OK")
        return True

    # ---------- ACTIONS ----------

    def browse(self):
        if self.frozen:
            return
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)
            self.cfg["install_dir"] = path
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, indent=4)
            self.startup_async()

    def install(self):
        self.frozen = True
        self.progress["value"] = 0
        self.log("INSTALL / REPAIR started")

        def run():
            asset = next(
                (a for a in self.latest_release["assets"] if a["name"] == FULL_INSTALL_ZIP),
                None
            )
            if not asset:
                self.log("ERROR: Full install ZIP missing from release")
                self.frozen = False
                self.startup_async()
                return

            download(asset["browser_download_url"], ZIP_PATH)

            with zipfile.ZipFile(ZIP_PATH) as z:
                files = z.namelist()
                for i, name in enumerate(files, 1):
                    z.extract(name, self.install_dir.get())
                    self.progress["value"] = (i / len(files)) * 100

            self.cfg["installed_version"] = normalize_version(
                self.latest_release["tag_name"]
            )
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, indent=4)

            self.log("INSTALL / REPAIR complete")
            self.frozen = False
            self.startup_async()

        threading.Thread(target=run, daemon=True).start()

    def ensure_game_save_dir(self, base):
        os.makedirs(os.path.join(base, GAME_SAVE_DIR_NAME), exist_ok=True)

    def launch(self):
        exe_path = os.path.join(self.install_dir.get(), GAME_EXE)

        if not os.path.exists(exe_path):
            self.log("ERROR: Game executable missing")
            return

        self.log("Launching game")
        subprocess.Popen([exe_path])

        if self.cfg["close_on_launch"]:
            self.destroy()

# =========================
# ENTRY
# =========================

if __name__ == "__main__":
    Launcher().mainloop()
