import os
import json
import time
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request
import urllib.error

APP_NAME = "Life RPG"
APP_VERSION = "1.3-alpha2"

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

CONFIG_DIR = os.path.join(
    os.environ.get("APPDATA", os.getcwd()),
    "LifeRPG"
)
CONFIG_FILE = os.path.join(CONFIG_DIR, "launcher.json")

SAVE_DIR_NAME = "life_rpg_save"
UPDATE_DIR_NAME = ".updates"
UPDATE_EXE_NAME = "LifeRPG_update.exe"


# ---------- Helpers ----------

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        return json.load(open(CONFIG_FILE, "r", encoding="utf-8"))
    except Exception:
        return {}


def save_config(data: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    json.dump(data, open(CONFIG_FILE, "w", encoding="utf-8"), indent=4)


def detect_install(path: str):
    version_file = os.path.join(path, "version.txt")
    if os.path.isdir(path) and os.path.exists(version_file):
        try:
            return True, open(version_file, "r", encoding="utf-8").read().strip()
        except Exception:
            return True, "unknown"
    return False, None


def fetch_latest_release():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


# ---------- Launcher ----------

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} Launcher")
        self.geometry("680x460")
        self.resizable(False, False)

        self.config_data = load_config()
        self.install_dir = tk.StringVar(
            value=self.config_data.get("install_dir", "")
        )
        self.status = tk.StringVar(value="Choose an install directory")
        self.update_status = tk.StringVar(value="Checking for updates…")

        ttk.Label(
            self,
            text=f"{APP_NAME} v{APP_VERSION}",
            font=("Segoe UI", 14)
        ).pack(pady=10)

        ttk.Entry(self, textvariable=self.install_dir, width=80).pack(padx=20)
        ttk.Button(self, text="Browse…", command=self.browse).pack(pady=5)

        ttk.Label(self, textvariable=self.update_status).pack(pady=5)

        self.progress = ttk.Progressbar(self, length=620)
        self.progress.pack(pady=10)

        ttk.Label(self, textvariable=self.status).pack(pady=5)

        self.buttons = ttk.Frame(self)
        self.buttons.pack(pady=10)

        ttk.Button(self, text="Save Directory", command=self.save_directory).pack()

        self.latest_release = None

        self.refresh_state()
        self.check_updates_async()

    # ---------- UI helpers ----------

    def browse(self):
        path = filedialog.askdirectory(title="Choose install directory")
        if path:
            self.install_dir.set(path)
            self.refresh_state()

    def save_directory(self):
        path = self.install_dir.get()
        if not path:
            messagebox.showerror("Error", "Choose a directory first.")
            return

        self.config_data["install_dir"] = path
        save_config(self.config_data)
        self.refresh_state()

    def refresh_state(self):
        for w in self.buttons.winfo_children():
            w.destroy()

        path = self.install_dir.get()
        installed, version = detect_install(path)

        if not path:
            self.status.set("No install directory selected")
            return

        if installed:
            self.status.set(f"Installed version: {version}")

            ttk.Button(self.buttons, text="Launch", command=self.launch).pack(side="left", padx=5)
            ttk.Button(self.buttons, text="Download Update", command=self.download_update).pack(side="left", padx=5)
            ttk.Button(self.buttons, text="Repair", command=self.repair).pack(side="left", padx=5)
        else:
            self.status.set("No install detected")
            ttk.Button(self.buttons, text="Install", command=self.install).pack()

    # ---------- Update logic ----------

    def check_updates_async(self):
        self.after(100, self.check_updates)

    def check_updates(self):
        self.latest_release = fetch_latest_release()
        if not self.latest_release:
            self.update_status.set("Unable to check for updates")
            return

        tag = self.latest_release.get("tag_name", "unknown")
        self.update_status.set(f"Latest version available: {tag}")

    def download_update(self):
        if not self.latest_release:
            messagebox.showerror("Error", "No update information available.")
            return

        threading.Thread(target=self._download_update_worker, daemon=True).start()

    def _download_update_worker(self):
        base = self.install_dir.get()
        updates_dir = os.path.join(base, UPDATE_DIR_NAME)
        os.makedirs(updates_dir, exist_ok=True)

        assets = self.latest_release.get("assets", [])
        exe_asset = next((a for a in assets if a["name"].lower().endswith(".exe")), None)

        if not exe_asset:
            self.update_status.set("No executable asset found in release")
            return

        url = exe_asset["browser_download_url"]
        dest = os.path.join(updates_dir, UPDATE_EXE_NAME)

        self.update_status.set("Downloading update…")
        self.progress["value"] = 0

        try:
            with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
                total = int(r.headers.get("Content-Length", 0))
                downloaded = 0

                while True:
                    chunk = r.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total:
                        percent = (downloaded / total) * 100
                        self.progress["value"] = percent

            self.update_status.set("Update downloaded (not applied yet)")
            messagebox.showinfo(
                "Download complete",
                "Update downloaded successfully.\n\n"
                "It has NOT been applied yet."
            )

        except Exception as e:
            self.update_status.set("Download failed")
            messagebox.showerror("Error", str(e))

    # ---------- Existing actions ----------

    def install(self):
        messagebox.showinfo("Install", "Install logic unchanged in alpha2.")

    def repair(self):
        messagebox.showinfo("Repair", "Repair logic unchanged in alpha2.")

    def launch(self):
        base = self.install_dir.get()
        exe_path = os.path.join(base, "LifeRPG.exe")

        if not os.path.exists(exe_path):
            messagebox.showerror("Launch Error", "LifeRPG.exe not found.")
            return

        subprocess.Popen(
            [exe_path],
            cwd=base,
            creationflags=subprocess.DETACHED_PROCESS
        )


if __name__ == "__main__":
    Launcher().mainloop()
