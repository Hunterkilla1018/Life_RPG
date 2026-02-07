import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_VERSION = "1.1.2"

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

    "game_logic.py": """def apply(player, tasks):
    for _ in tasks:
        player["xp"] += 10
    return player
""",

    "app_gui.py": """import tkinter as tk
from tkinter import ttk
from storage import load_player

class LifeRPGApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Life RPG v1.1.2")
        self.geometry("500x300")

        p = load_player()
        ttk.Label(self, text="Life RPG v1.1.2", font=("Segoe UI", 14)).pack(pady=20)
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

        self.title("Life RPG Installer")
        self.geometry("520x260")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.install_dir = tk.StringVar()
        self.status = tk.StringVar(value="Choose an installation folder")

        ttk.Label(self, text="Life RPG Installer (v1.1.2)", font=("Segoe UI", 14)).pack(pady=10)

        path_frame = ttk.Frame(self)
        path_frame.pack(pady=5)

        ttk.Entry(path_frame, textvariable=self.install_dir, width=45).pack(side="left", padx=5)
        ttk.Button(path_frame, text="Browse", command=self.browse).pack(side="left")

        self.progress = ttk.Progressbar(self, length=460)
        self.progress.pack(pady=15)

        ttk.Label(self, textvariable=self.status).pack()

        ttk.Button(self, text="Install", command=self.install).pack(pady=10)

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.install_dir.set(path)

    def install(self):
        base = self.install_dir.get()

        if not base:
            messagebox.showerror("Error", "Please choose an installation folder.")
            return

        os.makedirs(base, exist_ok=True)
        os.makedirs(os.path.join(base, "life_rpg_save"), exist_ok=True)

        self.progress["maximum"] = len(FILES)
        step = 0

        for name, content in FILES.items():
            self.status.set(f"Installing {name}...")
            self.update_idletasks()

            with open(os.path.join(base, name), "w", encoding="utf-8") as f:
                f.write(content)

            time.sleep(0.15)
            step += 1
            self.progress["value"] = step

        self.status.set("Launching Life RPG...")
        self.update_idletasks()
        time.sleep(0.4)

        self.destroy()
        subprocess.Popen([sys.executable, "main.py"], cwd=base)


if __name__ == "__main__":
    Installer().mainloop()
