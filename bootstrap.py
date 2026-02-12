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
# VERSION
# =========================

raw_version = os.environ.get("LAUNCHER_VERSION", "dev")
LAUNCHER_VERSION = raw_version.lstrip("v")

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

GAME_EXE = "LifeRPG.exe"
FULL_INSTALL_ZIP = "LifeRPG_full.zip"
PATCH_ZIP = "LifeRPG_patch.zip"
MANIFEST_NAME = "manifest.json"

APPDATA = os.path.join(os.environ.get("APPDATA", os.getcwd()), "LifeRPG")
RUNTIME = os.path.join(APPDATA, "runtime")
CONFIG_FILE = os.path.join(APPDATA, "launcher.json")

ZIP_PATH = os.path.join(RUNTIME, "download.zip")
RUNTIME_MANIFEST = os.path.join(RUNTIME, MANIFEST_NAME)

os.makedirs(RUNTIME, exist_ok=True)

# =========================
# HELPERS
# =========================

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_version(v):
    return v.lstrip("v").strip() if v else ""


def download(url, dest):
    urllib.request.urlretrieve(url, dest)


def fetch_latest_release():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode())


def load_config():
    cfg = {
        "install_dir": "",
        "installed_version": ""
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except:
            pass

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

    return cfg


# =========================
# LAUNCHER
# =========================

class Launcher(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title(f"Life RPG Launcher v{LAUNCHER_VERSION}")
        self.geometry("800x600")

        self.cfg = load_config()
        self.install_dir = tk.StringVar(value=self.cfg["install_dir"])
        self.latest_release = None
        self.manifest = None

        self._ui()
        self.after(100, self.startup)

    # ---------- UI ----------

    def _ui(self):
        ttk.Label(self, text=f"Life RPG Launcher v{LAUNCHER_VERSION}").pack(pady=10)

        self.console = tk.Text(self, height=18)
        self.console.pack(fill="both", expand=True)

        footer = ttk.Frame(self)
        footer.pack(pady=10)

        ttk.Entry(footer, textvariable=self.install_dir, width=60).pack(side="left")
        ttk.Button(footer, text="Browse", command=self.browse).pack(side="left")

        self.action_btn = ttk.Button(self, text="Checking...")
        self.action_btn.pack(pady=10)

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.console.insert("end", f"[{ts}] {msg}\n")
        self.console.see("end")

    # ---------- STARTUP ----------

    def startup(self):
        threading.Thread(target=self.check_state, daemon=True).start()

    def check_state(self):
        try:
            self.log("Checking GitHub release...")
            self.latest_release = fetch_latest_release()

            latest_version = normalize_version(self.latest_release["tag_name"])
            installed_version = normalize_version(self.cfg["installed_version"])

            self.log(f"Installed: {installed_version or 'none'}")
            self.log(f"Latest: {latest_version}")

            if not self.install_dir.get():
                self.set_action("Install", self.install_full)
                return

            if installed_version != latest_version:
                self.set_action("Update", self.update_game)
                return

            if not self.verify_integrity():
                self.log("Integrity failed. Repair required.")
                self.set_action("Repair", self.install_full)
                return

            self.set_action("Launch", self.launch)

        except Exception as e:
            self.log(f"Startup error: {e}")

    # ---------- MANIFEST ----------

    def load_manifest(self):
        asset = next(
            (a for a in self.latest_release["assets"] if a["name"] == MANIFEST_NAME),
            None
        )
        if not asset:
            self.log("Manifest missing from release.")
            return False

        download(asset["browser_download_url"], RUNTIME_MANIFEST)

        with open(RUNTIME_MANIFEST, "r", encoding="utf-8-sig") as f:
            self.manifest = json.load(f)

        return True

    def verify_integrity(self):
        install_path = self.install_dir.get()
        if not install_path:
            return False

        if not self.load_manifest():
            return False

        for rel, expected in self.manifest["files"].items():
            fp = os.path.join(install_path, rel)

            if not os.path.exists(fp):
                self.log(f"Missing file: {rel}")
                return False

            if sha256(fp) != expected:
                self.log(f"Hash mismatch: {rel}")
                return False

        self.log("Integrity verified.")
        return True

    # ---------- ACTIONS ----------

    def set_action(self, text, command):
        self.action_btn.config(
            text=text,
            command=lambda: threading.Thread(target=command, daemon=True).start()
        )

    def download_asset(self, name):
        asset = next(
            (a for a in self.latest_release["assets"] if a["name"] == name),
            None
        )
        if not asset:
            return False

        download(asset["browser_download_url"], ZIP_PATH)
        return True

    def apply_zip(self):
        try:
            install_path = self.install_dir.get()
            os.makedirs(install_path, exist_ok=True)

            with zipfile.ZipFile(ZIP_PATH) as z:
                z.extractall(install_path)

            self.log("Files applied.")
            return True

        except Exception as e:
            self.log(f"ZIP error: {e}")
            return False

    def install_full(self):
        self.log("Downloading full install...")

        if not self.download_asset(FULL_INSTALL_ZIP):
            self.log("Full install ZIP missing.")
            return

        if self.apply_zip():
            self.finalize_update()

    def update_game(self):
        self.log("Attempting patch update...")

        if self.download_asset(PATCH_ZIP):
            if self.apply_zip():
                self.finalize_update()
                return

        self.log("Patch unavailable or failed. Falling back to full install.")
        self.install_full()

    def finalize_update(self):
        new_version = normalize_version(self.latest_release["tag_name"])
        self.cfg["installed_version"] = new_version

        with open(CONFIG_FILE, "w") as f:
            json.dump(self.cfg, f, indent=4)

        self.log("Update complete.")
        self.set_action("Launch", self.launch)

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)
            self.cfg["install_dir"] = path
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.cfg, f, indent=4)

    def launch(self):
        exe = os.path.join(self.install_dir.get(), GAME_EXE)

        if not os.path.exists(exe):
            self.log("Game executable missing.")
            return

        subprocess.Popen([exe], cwd=self.install_dir.get())
        self.destroy()


if __name__ == "__main__":
    Launcher().mainloop()
