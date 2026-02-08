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
LAUNCHER_VERSION = "1.4.5-hotfix1"

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

GAME_EXE = "LifeRPG.exe"

# ============================================================
# Paths (CORRECTLY SEPARATED)
# ============================================================

APPDATA_BASE = os.path.join(os.environ["APPDATA"], "LifeRPG")
CONFIG_FILE = os.path.join(APPDATA_BASE, "launcher.json")

RUNTIME_DIR = os.path.join(APPDATA_BASE, "runtime")
UPDATE_EXE = os.path.join(RUNTIME_DIR, "LifeRPG_update.exe")
SWAP_SCRIPT = os.path.join(RUNTIME_DIR, "apply_update.bat")

os.makedirs(RUNTIME_DIR, exist_ok=True)

# ============================================================
# Helpers
# ============================================================

def load_config():
    default = {
        "install_dir": "",
        "close_on_launch": True,
        "minimize_on_launch": False,
        "update_interval_min": 1
    }

    if not os.path.exists(CONFIG_FILE):
        return default.copy()

    try:
        data = json.load(open(CONFIG_FILE, "r", encoding="utf-8"))
    except Exception:
        return default.copy()

    # 🔧 MIGRATE MISSING KEYS SAFELY
    changed = False
    for k, v in default.items():
        if k not in data:
            data[k] = v
            changed = True

    if changed:
        save_config(data)

    return data


def save_config(cfg):
    os.makedirs(APPDATA_BASE, exist_ok=True)
    json.dump(cfg, open(CONFIG_FILE, "w", encoding="utf-8"), indent=4)


def fetch_latest_release():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read().decode())


# ============================================================
# Launcher
# ============================================================

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} Launcher")
        self.geometry("820x580")
        self.resizable(False, False)

        self.config_data = load_config()

        self.install_dir = tk.StringVar(value=self.config_data.get("install_dir", ""))
        self.close_on_launch = tk.BooleanVar(value=self.config_data.get("close_on_launch", True))
        self.minimize_on_launch = tk.BooleanVar(value=self.config_data.get("minimize_on_launch", False))

        self.update_interval = self.config_data.get("update_interval_min", 1)

        self.latest_release = None
        self.update_state = "idle"
        self.game_running = False
        self.after_id = None

        self.build_ui()
        self.schedule_update_check()

    # --------------------------------------------------------

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x")

        ttk.Label(
            top,
            text=f"{APP_NAME} v{LAUNCHER_VERSION}",
            font=("Segoe UI", 14)
        ).pack(side="left", padx=10, pady=10)

        ttk.Button(top, text="⚙", command=self.open_settings)\
            .pack(side="right", padx=10)

        ttk.Entry(self, textvariable=self.install_dir, width=105).pack(pady=5)
        ttk.Button(self, text="Browse…", command=self.browse).pack()

        self.status = tk.StringVar(value="Idle")
        ttk.Label(self, textvariable=self.status).pack(pady=5)

        self.buttons = ttk.Frame(self)
        self.buttons.pack(pady=20)

        ttk.Button(self, text="Check now", command=self.manual_check).pack()

        self.refresh_buttons()

    # --------------------------------------------------------

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)
            self.config_data["install_dir"] = path
            save_config(self.config_data)
            self.refresh_buttons()

    # --------------------------------------------------------

    def open_settings(self):
        win = tk.Toplevel(self)
        win.title("Settings")
        win.geometry("360x260")
        win.resizable(False, False)

        close_cb = ttk.Checkbutton(
            win,
            text="Close launcher when game launches",
            variable=self.close_on_launch,
            command=self.save_settings
        )
        close_cb.pack(pady=10)

        minimize_cb = ttk.Checkbutton(
            win,
            text="Minimize launcher when game launches",
            variable=self.minimize_on_launch,
            command=self.save_settings
        )
        minimize_cb.pack(pady=5)

        if self.close_on_launch.get():
            minimize_cb.state(["disabled"])

        ttk.Label(win, text="Update check interval (minutes)").pack(pady=(15, 0))

        interval_box = ttk.Combobox(
            win,
            values=[1, 5, 15, 30, 60],
            state="readonly",
            width=10
        )
        interval_box.set(self.update_interval)
        interval_box.pack(pady=5)

        interval_box.bind(
            "<<ComboboxSelected>>",
            lambda e: self.update_interval_changed(interval_box.get())
        )

    def update_interval_changed(self, value):
        self.update_interval = int(value)
        self.config_data["update_interval_min"] = self.update_interval
        save_config(self.config_data)
        self.schedule_update_check()

    def save_settings(self):
        self.config_data["close_on_launch"] = self.close_on_launch.get()
        self.config_data["minimize_on_launch"] = self.minimize_on_launch.get()
        save_config(self.config_data)

    # --------------------------------------------------------

    def refresh_buttons(self):
        for w in self.buttons.winfo_children():
            w.destroy()

        base = self.install_dir.get()
        game = os.path.join(base, GAME_EXE)

        if not base or not os.path.exists(game):
            ttk.Button(self.buttons, text="Install", command=self.install).pack()
            return

        ttk.Button(self.buttons, text="Launch", command=self.launch).pack(side="left", padx=5)
        ttk.Button(self.buttons, text="Repair", command=self.repair).pack(side="left", padx=5)

        if self.update_state == "ready":
            ttk.Button(self.buttons, text="Apply Update", command=self.apply_update)\
                .pack(side="left", padx=5)

    # --------------------------------------------------------
    # Update logic
    # --------------------------------------------------------

    def schedule_update_check(self):
        if self.after_id:
            self.after_cancel(self.after_id)

        self.after_id = self.after(self.update_interval * 60_000, self.run_update_check)

    def run_update_check(self):
        if not self.game_running:
            threading.Thread(target=self.check_for_updates, daemon=True).start()
        self.schedule_update_check()

    def manual_check(self):
        if not self.game_running:
            threading.Thread(target=self.check_for_updates, daemon=True).start()

    def check_for_updates(self):
        self.update_state = "checking"
        self.status.set("Checking for updates…")

        self.latest_release = fetch_latest_release()
        self.update_state = "available"
        self.status.set("Update available — downloading")

        threading.Thread(target=self.download_update, daemon=True).start()

    def download_update(self):
        self.update_state = "downloading"
        self.status.set("Downloading update…")

        asset = next(a for a in self.latest_release["assets"] if a["name"] == GAME_EXE)
        url = asset["browser_download_url"]

        with urllib.request.urlopen(url) as r, open(UPDATE_EXE, "wb") as f:
            f.write(r.read())

        self.update_state = "ready"
        self.status.set("Update ready")
        self.refresh_buttons()

    # --------------------------------------------------------

    def apply_update(self):
        base = self.install_dir.get()
        game = os.path.join(base, GAME_EXE)

        with open(SWAP_SCRIPT, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
timeout /t 2 >nul
move "{UPDATE_EXE}" "{game}"
start "" "{game}"
""")

        subprocess.Popen(["cmd", "/c", SWAP_SCRIPT])
        self.handle_launcher_exit()

    # --------------------------------------------------------

    def install(self):
        self.check_for_updates()

    def repair(self):
        self.check_for_updates()

    def launch(self):
        self.game_running = True
        proc = subprocess.Popen([os.path.join(self.install_dir.get(), GAME_EXE)])
        self.handle_launcher_exit(proc)

    def handle_launcher_exit(self, proc=None):
        if self.close_on_launch.get():
            self.destroy()
        elif self.minimize_on_launch.get():
            self.iconify()
            if proc:
                threading.Thread(target=self.wait_for_game_exit, args=(proc,), daemon=True).start()

    def wait_for_game_exit(self, proc):
        proc.wait()
        self.game_running = False
        self.deiconify()
        self.status.set("Game closed — updates resumed")

# ============================================================
# Entry
# ============================================================

if __name__ == "__main__":
    Launcher().mainloop()
