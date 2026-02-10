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

APP_NAME = "Life RPG"
LAUNCHER_VERSION = "1.5.0-alpha8"

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

GAME_EXE = "LifeRPG.exe"
FULL_INSTALL_ZIP = "LifeRPG_full.zip"
MANIFEST_NAME = "manifest.json"

APPDATA = os.path.join(os.environ["APPDATA"], "LifeRPG")
RUNTIME = os.path.join(APPDATA, "runtime")
CONFIG_FILE = os.path.join(APPDATA, "launcher.json")
RUNTIME_MANIFEST = os.path.join(RUNTIME, MANIFEST_NAME)
ZIP_PATH = os.path.join(RUNTIME, FULL_INSTALL_ZIP)

os.makedirs(RUNTIME, exist_ok=True)

# ---------------- helpers ----------------

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
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            defaults.update(json.load(f))
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(defaults, f, indent=4)
    return defaults

def fetch_latest_release():
    with urllib.request.urlopen(
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest",
        timeout=10
    ) as r:
        return json.loads(r.read().decode())

def download(url, dest):
    urllib.request.urlretrieve(url, dest)

# ---------------- launcher ----------------

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LIFE RPG :: SYSTEM INTERFACE")
        self.geometry("1000x700")
        self.configure(bg="#0b0f14")

        self.cfg = load_config()
        self.install_dir = tk.StringVar(value=self.cfg["install_dir"])
        self.latest_release = None
        self.manifest = None
        self.frozen = False

        self.sys = tk.StringVar(value="INITIALIZING")
        self.net = tk.StringVar(value="UNKNOWN")
        self.integrity = tk.StringVar(value="UNKNOWN")
        self.update = tk.StringVar(value="UNKNOWN")

        self._ui()
        self.after(100, self.startup_async)

    # -------- logging --------

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.console.insert("end", f"[{ts}] {msg}\n")
        self.console.see("end")

    # -------- UI --------

    def _ui(self):
        tk.Label(
            self,
            text=f"LIFE RPG :: SYSTEM INTERFACE   v{LAUNCHER_VERSION}",
            fg="#7ddcff", bg="#0b0f14",
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
        ttk.Entry(footer, textvariable=self.install_dir, width=90).pack()
        ttk.Button(footer, text="Browse…", command=self.browse).pack()

        self.refresh_status()

    def refresh_status(self):
        self.status.config(
            text=f"SYSTEM: {self.sys.get()} | NET: {self.net.get()} | "
                 f"INTEGRITY: {self.integrity.get()} | UPDATE: {self.update.get()}"
        )

    def clear_actions(self):
        for w in self.actions.winfo_children():
            w.destroy()

    # -------- startup --------

    def startup_async(self):
        if self.frozen:
            return
        threading.Thread(target=self.startup_logic, daemon=True).start()

    def startup_logic(self):
        self.log("Startup check")
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

    # -------- states --------

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

    # -------- manifest / verify --------

    def load_manifest(self):
        asset = next(
            (a for a in self.latest_release["assets"] if a["name"] == MANIFEST_NAME),
            None
        )
        if not asset:
            self.log("Manifest missing from release")
            return False

        download(asset["browser_download_url"], RUNTIME_MANIFEST)
        with open(RUNTIME_MANIFEST, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

        with open(os.path.join(self.install_dir.get(), MANIFEST_NAME), "w") as f:
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

    # -------- actions --------

    def browse(self):
        if self.frozen:
            return
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)
            self.cfg["install_dir"] = path
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.cfg, f, indent=4)
            self.startup_async()

    def install(self):
        self.frozen = True
        self.progress["value"] = 0
        self.log("INSTALL/REPAIR start")

        def run():
            asset = next(
                (a for a in self.latest_release["assets"] if a["name"] == FULL_INSTALL_ZIP),
                None
            )
            if not asset:
                self.log("ERROR: Full install ZIP missing")
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
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.cfg, f, indent=4)

            self.log("INSTALL/REPAIR complete")
            self.frozen = False
            self.startup_async()

        threading.Thread(target=run, daemon=True).start()

    def launch(self):
        subprocess.Popen([os.path.join(self.install_dir.get(), GAME_EXE)])
        if self.cfg["close_on_launch"]:
            self.destroy()

# ---------------- entry ----------------

if __name__ == "__main__":
    Launcher().mainloop()
