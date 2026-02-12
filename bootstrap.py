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

LAUNCHER_VERSION = "1.6.0"

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

GAME_EXE = "LifeRPG.exe"
FULL_INSTALL_ZIP = "LifeRPG_full.zip"
PATCH_ZIP = "LifeRPG_patch.zip"
MANIFEST_NAME = "manifest.json"

# =========================
# PATHS
# =========================

APPDATA = os.path.join(os.environ.get("APPDATA", os.getcwd()), "LifeRPG")
RUNTIME = os.path.join(APPDATA, "runtime")
CONFIG_FILE = os.path.join(APPDATA, "launcher.json")

RUNTIME_MANIFEST = os.path.join(RUNTIME, MANIFEST_NAME)
ZIP_PATH = os.path.join(RUNTIME, "download.zip")

GAME_SAVE_DIR_NAME = "life_rpg_save"

os.makedirs(RUNTIME, exist_ok=True)

# =========================
# HELPERS
# =========================

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

    os.makedirs(APPDATA, exist_ok=True)

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

        self._ui()
        self.after(100, self.startup)

    # ---------- UI ----------

    def _ui(self):
        ttk.Label(self, text=f"Life RPG Launcher v{LAUNCHER_VERSION}").pack(pady=10)

        self.status = ttk.Label(self, text="")
        self.status.pack()

        self.console = tk.Text(self, height=15)
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
        threading.Thread(target=self.check_updates, daemon=True).start()

    def check_updates(self):
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
            else:
                self.set_action("Launch", self.launch)

        except Exception as e:
            self.log(f"Startup error: {e}")

    def set_action(self, text, command):
        self.action_btn.config(
            text=text,
            command=lambda: threading.Thread(target=command, daemon=True).start()
        )

    # =========================
    # UPDATE LOGIC
    # =========================

    def download_asset(self, name):
        asset = next(
            (a for a in self.latest_release["assets"] if a["name"] == name),
            None
        )
        if not asset:
            return False

        download(asset["browser_download_url"], ZIP_PATH)
        return True

    def update_game(self):
        self.log("Attempting patch update...")

        patch_asset = next(
            (a for a in self.latest_release["assets"]
             if a["name"] == PATCH_ZIP),
            None
        )

        # Try patch first
        if patch_asset:
            try:
                download(patch_asset["browser_download_url"], ZIP_PATH)
                if self.apply_zip(ZIP_PATH):
                    self.finalize_update()
                    return
            except Exception as e:
                self.log(f"Patch failed: {e}")

        # Fallback to full install
        self.log("Falling back to full install...")

        full_asset = next(
            (a for a in self.latest_release["assets"]
             if a["name"] == FULL_INSTALL_ZIP),
            None
        )

        if not full_asset:
            self.log("ERROR: Full install ZIP missing from release.")
            return

        download(full_asset["browser_download_url"], ZIP_PATH)

        if self.apply_zip(ZIP_PATH):
            self.finalize_update()

    def install_full(self):
        self.log("Downloading full install...")

        if not self.download_asset(FULL_INSTALL_ZIP):
            self.log("ERROR: Full install ZIP missing.")
            return

        if self.apply_zip(ZIP_PATH):
            self.finalize_update()

    def apply_zip(self, zip_path):
        try:
            with zipfile.ZipFile(zip_path) as z:
                for name in z.namelist():
                    if GAME_SAVE_DIR_NAME in name:
                        continue
                    z.extract(name, self.install_dir.get())

            self.log("Files applied successfully.")
            return True

        except Exception as e:
            self.log(f"ZIP ERROR: {e}")
            return False

    def finalize_update(self):
        new_version = normalize_version(self.latest_release["tag_name"])
        self.cfg["installed_version"] = new_version

        with open(CONFIG_FILE, "w") as f:
            json.dump(self.cfg, f, indent=4)

        self.log("Update complete.")

        # Refresh UI state cleanly after update
        self.set_action("Launch", self.launch)


    # =========================
    # ACTIONS
    # =========================

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)
            self.cfg["install_dir"] = path
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.cfg, f, indent=4)

    def launch(self):
        exe = os.path.join(self.install_dir.get(), GAME_EXE)

        if os.path.exists(exe):
            subprocess.Popen([exe])
            self.destroy()
        else:
            self.log("Game executable missing.")

# =========================
# ENTRY (WITH CRASH LOGGING)
# =========================

if __name__ == "__main__":
    try:
        Launcher().mainloop()
    except Exception as e:
        with open("launcher_error.log", "w") as f:
            f.write(str(e))
        raise
