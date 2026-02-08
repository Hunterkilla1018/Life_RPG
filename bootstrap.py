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
LAUNCHER_VERSION = "1.5.0-alpha1-hotfix4"

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

def normalize_version(v: str) -> str:
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
        self.resizable(False, False)
        self.configure(bg="#0b0f14")

        self.cfg = load_config()
        self.install_dir = tk.StringVar(value=self.cfg["install_dir"])

        self.latest_release = None
        self.manifest = None

        # System state
        self.sys_status = tk.StringVar(value="INITIALIZING")
        self.net_status = tk.StringVar(value="UNKNOWN")
        self.integrity_status = tk.StringVar(value="UNKNOWN")
        self.update_status = tk.StringVar(value="UNKNOWN")

        self._build_ui()
        self.after(100, self.startup_check_async)

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):
        header = tk.Frame(self, bg="#0b0f14")
        header.pack(fill="x", padx=15, pady=(15, 5))

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
        self.status_label.pack(fill="x", padx=15, pady=(0, 10))
        self._refresh_status_bar()

        self.primary_action_frame = ttk.Frame(self)
        self.primary_action_frame.pack(pady=40)

        footer = ttk.Frame(self)
        footer.pack(side="bottom", pady=10)

        ttk.Entry(footer, textvariable=self.install_dir, width=100).pack()
        ttk.Button(footer, text="Browse…", command=self.browse).pack(pady=5)

    def _refresh_status_bar(self):
        self.status_label.config(
            text=(
                f"SYSTEM: {self.sys_status.get()}   |   "
                f"NET: {self.net_status.get()}   |   "
                f"INTEGRITY: {self.integrity_status.get()}   |   "
                f"UPDATE: {self.update_status.get()}"
            )
        )

    def clear_primary_actions(self):
        for w in self.primary_action_frame.winfo_children():
            w.destroy()

    # ========================================================
    # Startup Logic
    # ========================================================

    def startup_check_async(self):
        threading.Thread(target=self._startup_logic, daemon=True).start()

    def _startup_logic(self):
        net_ok = internet_available()
        self.net_status.set("OK" if net_ok else "OFFLINE")

        if not net_ok:
            self.after(0, lambda: self.apply_state("NO_INTERNET"))
            return

        self.latest_release = fetch_latest_release()
        latest = normalize_version(self.latest_release.get("tag_name"))
        installed = normalize_version(self.cfg.get("installed_version"))

        base = self.install_dir.get()
        game = os.path.join(base, GAME_EXE)

        if not base or not os.path.exists(game):
            self.after(0, lambda: self.apply_state("NOT_INSTALLED"))
            return

        if not installed or installed != latest:
            self.after(0, lambda: self.apply_state("UPDATE_REQUIRED"))
            return

        self._download_manifest_safe()

        if not self.manifest:
            self.after(0, lambda: self.apply_state("MANIFEST_MISSING"))
            return

        if not self.verify_integrity(game):
            self.after(0, lambda: self.apply_state("INTEGRITY_FAILED"))
            return

        self.after(0, lambda: self.apply_state("READY"))

    # ========================================================
    # State Application
    # ========================================================

    def apply_state(self, state):
        self.clear_primary_actions()

        if state == "NO_INTERNET":
            self.sys_status.set("BLOCKED")
            self.update_status.set("OFFLINE")
            self.integrity_status.set("UNKNOWN")

        elif state == "NOT_INSTALLED":
            self.sys_status.set("BLOCKED")
            self.update_status.set("INSTALL REQUIRED")
            self.integrity_status.set("UNKNOWN")
            ttk.Button(self.primary_action_frame, text="INSTALL SYSTEM",
                       command=self.install).pack()

        elif state == "UPDATE_REQUIRED":
            self.sys_status.set("BLOCKED")
            self.update_status.set("REQUIRED")
            self.integrity_status.set("UNKNOWN")
            ttk.Button(self.primary_action_frame, text="DOWNLOAD UPDATE",
                       command=self.download_update).pack()

        elif state == "MANIFEST_MISSING":
            self.sys_status.set("BLOCKED")
            self.update_status.set("MANIFEST MISSING")
            self.integrity_status.set("UNKNOWN")
            ttk.Button(self.primary_action_frame, text="DOWNLOAD UPDATE",
                       command=self.download_update).pack()

        elif state == "INTEGRITY_FAILED":
            self.sys_status.set("BLOCKED")
            self.update_status.set("REPAIR REQUIRED")
            self.integrity_status.set("FAILED")
            ttk.Button(self.primary_action_frame, text="REPAIR SYSTEM",
                       command=self.repair).pack()

        elif state == "READY":
            self.sys_status.set("READY")
            self.update_status.set("NONE")
            self.integrity_status.set("VERIFIED")
            ttk.Button(self.primary_action_frame, text="LAUNCH SYSTEM",
                       command=self.launch).pack()

        self._refresh_status_bar()

    # ========================================================
    # Manifest & Integrity
    # ========================================================

    def _download_manifest_safe(self):
        assets = self.latest_release.get("assets", [])
        asset = next((a for a in assets if a.get("name") == MANIFEST_NAME), None)

        if not asset:
            self.manifest = None
            return

        download(asset["browser_download_url"], MANIFEST_PATH)
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def verify_integrity(self, game_path):
        expected = self.manifest.get("files", {}).get(GAME_EXE)
        return expected and sha256(game_path) == expected

    # ========================================================
    # Actions
    # ========================================================

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)
            self.cfg["install_dir"] = path
            save_config(self.cfg)
            self.startup_check_async()

    def download_update(self):
        self.clear_primary_actions()
        self.update_status.set("DOWNLOADING")
        self._refresh_status_bar()

        def _download():
            assets = self.latest_release.get("assets", [])
            asset = next((a for a in assets if a.get("name") == GAME_EXE), None)

            if not asset:
                self.after(0, lambda: self.apply_state("UPDATE_REQUIRED"))
                return

            try:
                download(asset["browser_download_url"], UPDATE_EXE)
            except Exception:
                self.after(0, lambda: self.apply_state("UPDATE_REQUIRED"))
                return

            self.after(0, self.show_apply_update_button)

        threading.Thread(target=_download, daemon=True).start()

    def show_apply_update_button(self):
        self.clear_primary_actions()
        self.update_status.set("READY")
        self._refresh_status_bar()
        ttk.Button(self.primary_action_frame, text="APPLY UPDATE",
                   command=self.apply_update).pack()

    def apply_update(self):
        game = os.path.join(self.install_dir.get(), GAME_EXE)

        with open(SWAP_SCRIPT, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
timeout /t 2 >nul
move "{UPDATE_EXE}" "{game}"
""")

        def _apply_and_verify():
            subprocess.call(["cmd", "/c", SWAP_SCRIPT])

            if not os.path.exists(game):
                self.after(0, lambda: self.apply_state("UPDATE_REQUIRED"))
                return

            self.cfg["installed_version"] = normalize_version(
                self.latest_release["tag_name"]
            )
            save_config(self.cfg)

            self.after(0, self.destroy)

        threading.Thread(target=_apply_and_verify, daemon=True).start()

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
