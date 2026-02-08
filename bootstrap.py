import os
import json
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request

# ============================================================
# Identity
# ============================================================

APP_NAME = "Life RPG"
LAUNCHER_VERSION = "1.3.3"

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

GAME_EXE = "LifeRPG.exe"
LAUNCHER_EXE = "LifeRPG_Launcher.exe"

UPDATE_DIR = ".updates"
UPDATE_EXE = "LifeRPG_update.exe"
SWAP_SCRIPT = "apply_update.bat"

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.getcwd()), "LifeRPG")
CONFIG_FILE = os.path.join(CONFIG_DIR, "launcher.json")


# ============================================================
# Managed file: storage.py
# ============================================================

STORAGE_PY_CONTENT = """\
import os
import json

try:
    from cryptography.fernet import Fernet
except ImportError as e:
    raise RuntimeError(
        "Cryptography dependency missing.\\n\\n"
        "The game was not packaged correctly.\\n"
        "Please reinstall or update Life RPG."
    ) from e


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


def write_storage_py(install_dir: str):
    with open(os.path.join(install_dir, "storage.py"), "w", encoding="utf-8") as f:
        f.write(STORAGE_PY_CONTENT)


# ============================================================
# Helpers
# ============================================================

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


def installed_game_version(path):
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


# ============================================================
# Launcher
# ============================================================

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} Launcher")
        self.geometry("760x520")
        self.resizable(False, False)

        self.config = load_config()
        self.install_dir = tk.StringVar(value=self.config.get("install_dir", ""))
        self.status = tk.StringVar(value="Choose install directory")
        self.update_status = tk.StringVar(value="Checking for updates…")

        self.latest_release = None
        self.update_available = False

        ttk.Label(
            self,
            text=f"{APP_NAME} Launcher v{LAUNCHER_VERSION}",
            font=("Segoe UI", 14)
        ).pack(pady=10)

        ttk.Entry(self, textvariable=self.install_dir, width=95).pack()
        ttk.Button(self, text="Browse…", command=self.browse).pack(pady=5)

        ttk.Label(self, textvariable=self.update_status).pack(pady=5)

        self.progress = ttk.Progressbar(self, length=720)
        self.progress.pack(pady=10)

        ttk.Label(self, textvariable=self.status).pack(pady=5)

        self.buttons = ttk.Frame(self)
        self.buttons.pack(pady=10)

        ttk.Button(self, text="Save Directory", command=self.save_directory).pack()

        self.after(100, self.check_updates)
        self.refresh_state()

    # --------------------------------------------------------

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

    # --------------------------------------------------------

    def refresh_state(self):
        for w in self.buttons.winfo_children():
            w.destroy()

        base = self.install_dir.get()
        version = installed_game_version(base)

        if not base:
            self.status.set("No install directory selected")
            return

        if version:
            self.status.set(f"Installed game version: {version}")

            ttk.Button(
                self.buttons,
                text="Launch Game",
                command=self.launch
            ).pack(side="left", padx=5)

            if self.update_available:
                ttk.Button(
                    self.buttons,
                    text="Update",
                    command=lambda: self.install_or_update("update")
                ).pack(side="left", padx=5)

            ttk.Button(
                self.buttons,
                text="Repair",
                command=lambda: self.install_or_update("repair")
            ).pack(side="left", padx=5)

        else:
            self.status.set("Game not installed")
            ttk.Button(
                self.buttons,
                text="Install",
                command=lambda: self.install_or_update("install")
            ).pack()

    # --------------------------------------------------------

    def check_updates(self):
        self.latest_release = fetch_latest_release()
        base = self.install_dir.get()
        installed = installed_game_version(base)

        if not self.latest_release:
            self.update_status.set("Unable to check for updates")
            return

        latest = self.latest_release.get("tag_name")

        if installed == latest:
            self.update_available = False
            self.update_status.set("You are up to date")
        else:
            self.update_available = True
            self.update_status.set(f"Update available: {latest}")

        self.refresh_state()

    # --------------------------------------------------------

    def install_or_update(self, mode: str):
        if not self.latest_release:
            messagebox.showerror("Error", "No release information available.")
            return

        threading.Thread(
            target=self._download_and_apply,
            args=(mode,),
            daemon=True
        ).start()

    def _download_and_apply(self, mode: str):
        base = self.install_dir.get()
        updates = os.path.join(base, UPDATE_DIR)
        os.makedirs(updates, exist_ok=True)

        asset = next(
            (a for a in self.latest_release["assets"] if a["name"] == GAME_EXE),
            None
        )

        if not asset:
            messagebox.showerror("Error", "LifeRPG.exe not found in release.")
            return

        url = asset["browser_download_url"]
        dest = os.path.join(updates, UPDATE_EXE)

        self.progress["value"] = 0
        self.update_status.set(f"{mode.capitalize()}ing game…")

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

        write_storage_py(base)

        with open(os.path.join(base, "version.txt"), "w", encoding="utf-8") as f:
            f.write(self.latest_release.get("tag_name", "unknown"))

        self._apply_update(mode)

    # --------------------------------------------------------

    def _apply_update(self, mode: str):
        base = self.install_dir.get()
        updates = os.path.join(base, UPDATE_DIR)

        new_exe = os.path.join(updates, UPDATE_EXE)
        old_exe = os.path.join(base, GAME_EXE)
        backup = old_exe + ".bak"

        launch_game = (mode != "repair")

        script = os.path.join(updates, SWAP_SCRIPT)
        with open(script, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
timeout /t 2 >nul
if exist "{backup}" del "{backup}"
if exist "{old_exe}" ren "{old_exe}" "{GAME_EXE}.bak"
move "{new_exe}" "{old_exe}"
{"start \"\" \"" + old_exe + "\"" if launch_game else ""}
""")

        subprocess.Popen(["cmd", "/c", script], cwd=updates)

        if mode == "repair":
            self.progress["value"] = 0
            self.update_status.set("Repair complete")
            self.check_updates()
        else:
            self.destroy()

    # --------------------------------------------------------

    def launch(self):
        base = self.install_dir.get()
        game = os.path.join(base, GAME_EXE)
        launcher = os.path.join(base, LAUNCHER_EXE)

        if not os.path.exists(game):
            messagebox.showerror("Launch Error", "Game not installed.")
            return

        if os.path.abspath(game) == os.path.abspath(launcher):
            messagebox.showerror("Critical Error", "Launcher attempted to launch itself.")
            return

        subprocess.Popen([game], cwd=base)


# ============================================================
# Entry
# ============================================================

if __name__ == "__main__":
    Launcher().mainloop()
