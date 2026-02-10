# --- existing imports unchanged ---
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

LAUNCHER_VERSION = "1.5.0-alpha11"  # [lifeRPG update]

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

GAME_EXE = "LifeRPG.exe"
FULL_INSTALL_ZIP = "LifeRPG_full.zip"
MANIFEST_NAME = "manifest.json"

# =========================
# PATHS
# =========================

APPDATA = os.path.join(os.environ["APPDATA"], "LifeRPG")
RUNTIME = os.path.join(APPDATA, "runtime")
CONFIG_FILE = os.path.join(APPDATA, "launcher.json")
RUNTIME_MANIFEST = os.path.join(RUNTIME, MANIFEST_NAME)
ZIP_PATH = os.path.join(RUNTIME, FULL_INSTALL_ZIP)

# [lifeRPG update] Game-owned save directory
GAME_SAVE_DIR_NAME = "life_rpg_save"

os.makedirs(RUNTIME, exist_ok=True)

# =========================
# HELPERS (unchanged)
# =========================
# normalize_version, sha256, internet_available, load_config, fetch_latest_release, download
# (no changes here)

# =========================
# LAUNCHER
# =========================

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Life RPG :: Launcher")
        self.geometry("900x650")
        self.configure(bg="#0b0f14")

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
    # (_ui, refresh_status, clear_actions unchanged)

    # ---------- STARTUP ----------

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

        # [lifeRPG update] Ensure save directory exists
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

    # ---------- lifeRPG HELPERS ----------

    def ensure_game_save_dir(self, install_base):
        save_dir = os.path.join(install_base, GAME_SAVE_DIR_NAME)
        try:
            os.makedirs(save_dir, exist_ok=True)
            self.log(f"Save directory OK: {save_dir}")
        except Exception as e:
            self.log(f"WARNING: Could not create save dir ({e})")

    # ---------- STATES ----------
    # (unchanged)

    # ---------- MANIFEST ----------
    # (unchanged)

    # ---------- ACTIONS ----------
    # browse, install unchanged

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
