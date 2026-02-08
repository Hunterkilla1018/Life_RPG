import os
import json
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request

APP_NAME = "Life RPG"
APP_VERSION = "1.3-alpha3"

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.getcwd()), "LifeRPG")
CONFIG_FILE = os.path.join(CONFIG_DIR, "launcher.json")

UPDATE_DIR = ".updates"
UPDATE_EXE = "LifeRPG_update.exe"
GAME_EXE = "LifeRPG.exe"
LAUNCHER_EXE = "LifeRPG_Launcher.exe"
SWAP_SCRIPT = "apply_update.bat"


# ---------------- Config ----------------

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        return json.load(open(CONFIG_FILE, "r", encoding="utf-8"))
    except Exception:
        return {}


def save_config(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    json.dump(data, open(CONFIG_FILE, "w", encoding="utf-8"), indent=4)


def detect_version(path):
    try:
        with open(os.path.join(path, "version.txt"), "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


def fetch_latest_release():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


# ---------------- Launcher ----------------

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} Launcher")
        self.geometry("720x500")
        self.resizable(False, False)

        self.config = load_config()
        self.install_dir = tk.StringVar(value=self.config.get("install_dir", ""))
        self.status = tk.StringVar(value="Choose install directory")
        self.update_status = tk.StringVar(value="Checking for updates…")

        ttk.Label(self, text=f"{APP_NAME} {APP_VERSION}", font=("Segoe UI", 14)).pack(pady=10)

        ttk.Entry(self, textvariable=self.install_dir, width=90).pack()
        ttk.Button(self, text="Browse…", command=self.browse).pack(pady=5)

        ttk.Label(self, textvariable=self.update_status).pack(pady=5)

        self.progress = ttk.Progressbar(self, length=680)
        self.progress.pack(pady=10)

        ttk.Label(self, textvariable=self.status).pack(pady=5)

        self.buttons = ttk.Frame(self)
        self.buttons.pack(pady=10)

        ttk.Button(self, text="Save Directory", command=self.save_directory).pack()

        self.latest_release = None
        self.after(100, self.check_updates)

        self.refresh_state()

    # ---------- UI ----------

    def browse(self):
        path = filedialog.askdirectory(title="Choose install directory")
        if path:
            self.install_dir.set(path)
            self.refresh_state()

    def save_directory(self):
        path = self.install_dir.get()
        if not path:
            return
        self.config["install_dir"] = path
        save_config(self.config)
        self.refresh_state()

    def refresh_state(self):
        for w in self.buttons.winfo_children():
            w.destroy()

        base = self.install_dir.get()
        installed_version = detect_version(base)

        if not base:
            self.status.set("No install directory selected")
            return

        if installed_version:
            self.status.set(f"Installed version: {installed_version}")

            ttk.Button(self.buttons, text="Launch", command=self.launch).pack(side="left", padx=5)
            ttk.Button(self.buttons, text="Download Update", command=self.download_update).pack(side="left", padx=5)

            if os.path.exists(os.path.join(base, UPDATE_DIR, UPDATE_EXE)):
                ttk.Button(self.buttons, text="Apply Update", command=self.apply_update).pack(side="left", padx=5)
        else:
            self.status.set("No install detected")

    # ---------- Updates ----------

    def check_updates(self):
        self.latest_release = fetch_latest_release()
        base = self.install_dir.get()
        installed = detect_version(base)

        if not self.latest_release:
            self.update_status.set("Unable to check for updates")
            return

        latest = self.latest_release.get("tag_name")

        if installed == latest:
            self.update_status.set("You are up to date")
        else:
            self.update_status.set(f"Update available: {latest}")

    def download_update(self):
        if not self.latest_release:
            return
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        base = self.install_dir.get()
        updates = os.path.join(base, UPDATE_DIR)
        os.makedirs(updates, exist_ok=True)

        exe_asset = next(
            a for a in self.latest_release["assets"]
            if a["name"].endswith(".exe")
        )

        url = exe_asset["browser_download_url"]
        dest = os.path.join(updates, UPDATE_EXE)

        self.progress["value"] = 0
        self.update_status.set("Downloading update…")

        with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
            total = int(r.headers.get("Content-Length", 0))
            read = 0
            while True:
                chunk = r.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                read += len(chunk)
                if total:
                    self.progress["value"] = (read / total) * 100

        self.update_status.set("Update downloaded — ready to apply")
        self.refresh_state()

    # ---------- Apply ----------

    def apply_update(self):
        base = self.install_dir.get()
        updates = os.path.join(base, UPDATE_DIR)

        new_exe = os.path.join(updates, UPDATE_EXE)
        old_exe = os.path.join(base, GAME_EXE)
        backup = old_exe + ".bak"

        script = os.path.join(updates, SWAP_SCRIPT)
        with open(script, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
timeout /t 2 >nul
if exist "{backup}" del "{backup}"
if exist "{old_exe}" ren "{old_exe}" "{GAME_EXE}.bak"
move "{new_exe}" "{old_exe}"
start "" "{old_exe}"
""")

        subprocess.Popen(["cmd", "/c", script], cwd=updates)
        self.destroy()

    # ---------- Launch ----------

    def launch(self):
        base = self.install_dir.get()
        exe = os.path.join(base, GAME_EXE)

        if not os.path.exists(exe):
            messagebox.showerror("Launch Error", "LifeRPG.exe not found.")
            return

        subprocess.Popen([exe], cwd=base)


if __name__ == "__main__":
    Launcher().mainloop()
