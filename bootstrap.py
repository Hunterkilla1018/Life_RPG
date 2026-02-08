import os
import json
import time
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "Life RPG"
APP_VERSION = "1.2"

CONFIG_DIR = os.path.join(
    os.environ.get("APPDATA", os.getcwd()),
    "LifeRPG"
)
CONFIG_FILE = os.path.join(CONFIG_DIR, "launcher.json")

SAVE_DIR_NAME = "life_rpg_save"

# --- REAL app files (minimal but valid) ---
APP_FILES = {
    "main.py": """from app_gui import LifeRPGApp
LifeRPGApp().mainloop()
""",

    "app_gui.py": """import tkinter as tk
from tkinter import ttk
from storage import load_player

class LifeRPGApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Life RPG")
        self.geometry("500x300")

        player = load_player()

        ttk.Label(self, text="Life RPG", font=("Segoe UI", 14)).pack(pady=20)
        ttk.Label(
            self,
            text=f"Level: {player['level']}  XP: {player['xp']}"
        ).pack()
""",

    "storage.py": """import os, json

SAVE_DIR = "life_rpg_save"
PLAYER_FILE = os.path.join(SAVE_DIR, "player.json")

os.makedirs(SAVE_DIR, exist_ok=True)

def load_player():
    if not os.path.exists(PLAYER_FILE):
        return {"level": 1, "xp": 0}
    return json.load(open(PLAYER_FILE))

def save_player(player):
    json.dump(player, open(PLAYER_FILE, "w"), indent=4)
""",

    "game_logic.py": """def apply(player, tasks):
    for _ in tasks:
        player["xp"] += 10
    return player
""",

    "version.txt": APP_VERSION + "\n",
}

# ---------------- Utility ----------------

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


# ---------------- Launcher ----------------

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} Launcher")
        self.geometry("620x400")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.safe_exit)

        self.config_data = load_config()
        self.install_dir = tk.StringVar(
            value=self.config_data.get("install_dir", "")
        )
        self.status = tk.StringVar(value="Choose an install directory")

        ttk.Label(
            self,
            text=f"{APP_NAME} v{APP_VERSION}",
            font=("Segoe UI", 14)
        ).pack(pady=10)

        ttk.Entry(self, textvariable=self.install_dir, width=75).pack(padx=20)
        ttk.Button(self, text="Browse…", command=self.browse).pack(pady=5)

        self.progress = ttk.Progressbar(self, length=560)
        self.progress.pack(pady=10)

        ttk.Label(self, textvariable=self.status).pack(pady=5)

        self.buttons = ttk.Frame(self)
        self.buttons.pack(pady=10)

        ttk.Button(self, text="Save Directory", command=self.save_directory).pack()

        self.refresh_state()

    def safe_exit(self):
        self.destroy()

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
            self.status.set(f"Installed version detected: {version}")

            ttk.Button(self.buttons, text="Launch", command=self.launch).pack(side="left", padx=5)
            ttk.Button(self.buttons, text="Update", command=self.update).pack(side="left", padx=5)
            ttk.Button(self.buttons, text="Repair", command=self.repair).pack(side="left", padx=5)
        else:
            self.status.set("No install detected")
            ttk.Button(self.buttons, text="Install", command=self.install).pack()

    # -------- Actions --------

    def install(self):
        self.run_file_write("install")

    def update(self):
        self.run_file_write("update")

    def repair(self):
        self.run_file_write("repair")

    def run_file_write(self, mode: str):
        base = self.install_dir.get()
        if not base:
            return

        os.makedirs(base, exist_ok=True)
        os.makedirs(os.path.join(base, SAVE_DIR_NAME), exist_ok=True)

        self.progress["maximum"] = len(APP_FILES)
        self.progress["value"] = 0

        for i, (name, content) in enumerate(APP_FILES.items(), start=1):
            self.status.set(f"{mode.capitalize()}ing {name}…")
            self.update_idletasks()

            with open(os.path.join(base, name), "w", encoding="utf-8") as f:
                f.write(content)

            time.sleep(0.15)
            self.progress["value"] = i

        self.status.set(f"{mode.capitalize()} complete")
        messagebox.showinfo("Done", f"{mode.capitalize()} completed successfully.")
        self.refresh_state()

    def launch(self):
        base = self.install_dir.get()
        if not base:
            return

        main_path = os.path.join(base, "main.py")
        if not os.path.exists(main_path):
            messagebox.showerror("Error", "main.py not found. Try Repair.")
            return

        subprocess.Popen(
            ["python", "main.py"],
            cwd=base,
            creationflags=subprocess.DETACHED_PROCESS
        )


if __name__ == "__main__":
    Launcher().mainloop()
