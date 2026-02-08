import os
import sys
import json
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "Life RPG"
APP_VERSION = "1.1.9"

CONFIG_FILE = os.path.join(
    os.environ.get("APPDATA", os.getcwd()),
    "LifeRPG_launcher.json"
)

FILES = {
    "config.py": """APP_NAME = "Life RPG"
SAVE_DIR = "life_rpg_save"
""",

    "storage.py": """import os, json
from config import SAVE_DIR

os.makedirs(SAVE_DIR, exist_ok=True)
PLAYER_FILE = os.path.join(SAVE_DIR, "player.json")

def load_player():
    if not os.path.exists(PLAYER_FILE):
        return {"level": 1, "xp": 0}
    return json.load(open(PLAYER_FILE))

def save_player(p):
    json.dump(p, open(PLAYER_FILE, "w"), indent=4)
""",

    "api_ticktick.py": """import requests
BASE = "https://api.ticktick.com/open/v1"

def fetch_tasks(token):
    r = requests.post(
        f"{BASE}/task/query",
        headers={"Authorization": f"Bearer {token}"},
        json={}
    )
    return r.json().get("tasks", [])
""",

    "game_logic.py": """def apply(player, tasks):
    for _ in tasks:
        player["xp"] += 10
    return player
""",

    "app_gui.py": """import tkinter as tk
from tkinter import ttk
from storage import load_player, save_player

class LifeRPGApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Life RPG")
        self.geometry("500x300")

        p = load_player()
        ttk.Label(self, text="Life RPG", font=("Segoe UI", 14)).pack(pady=20)
        ttk.Label(self, text=f"Level: {p['level']}  XP: {p['xp']}").pack()
""",

    "main.py": """from app_gui import LifeRPGApp
LifeRPGApp().mainloop()
""",

    "version.txt": APP_VERSION
}


class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} Installer")
        self.geometry("540x320")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.install_dir = tk.StringVar()
        self.status = tk.StringVar(value="Choose an install directory")

        ttk.Label(
            self,
            text=f"{APP_NAME} Installer v{APP_VERSION}",
            font=("Segoe UI", 14)
        ).pack(pady=10)

        ttk.Entry(self, textvariable=self.install_dir, width=55).pack()
        ttk.Button(self, text="Browse", command=self.browse).pack(pady=5)

        self.bar = ttk.Progressbar(self, length=480)
        self.bar.pack(pady=10)

        ttk.Label(self, textvariable=self.status).pack(pady=5)
        ttk.Button(self, text="Install", command=self.install).pack(pady=10)

        self.load_previous_path()

    def load_previous_path(self):
        if os.path.exists(CONFIG_FILE):
            try:
                data = json.load(open(CONFIG_FILE))
                self.install_dir.set(data.get("install_dir", ""))
            except Exception:
                pass

    def save_path(self, path):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        json.dump({"install_dir": path}, open(CONFIG_FILE, "w"), indent=4)

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)

    def install(self):
        base = self.install_dir.get()
        if not base:
            messagebox.showerror("Error", "Please choose an install folder")
            return

        os.makedirs(base, exist_ok=True)
        self.save_path(base)

        self.bar["maximum"] = len(FILES)
        step = 0

        for name, content in FILES.items():
            self.status.set(f"Installing {name}...")
            self.update_idletasks()

            with open(os.path.join(base, name), "w", encoding="utf-8") as f:
                f.write(content)

            time.sleep(0.15)
            step += 1
            self.bar["value"] = step

        os.makedirs(os.path.join(base, "life_rpg_save"), exist_ok=True)

        self.status.set("Installation complete")
        self.update_idletasks()

        messagebox.showinfo(
            "Installed",
            "Life RPG has been installed successfully.\n\n"
            "You can now close this installer and run the app."
        )

        self.destroy()
        sys.exit(0)


if __name__ == "__main__":
    Installer().mainloop()
