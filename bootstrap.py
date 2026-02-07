import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import time

APP_VERSION = "1.1"

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
        return {"level":1,"xp":0}
    return json.load(open(PLAYER_FILE))

def save_player(p):
    json.dump(p, open(PLAYER_FILE,"w"), indent=4)
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
    for t in tasks:
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

        ttk.Label(self, text="Life RPG v1.1").pack(pady=20)

        p = load_player()
        ttk.Label(self, text=f"Level: {p['level']} XP: {p['xp']}").pack()
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

        ttk.Label(self, text="Choose installation folder").pack(pady=10)
        ttk.Entry(self, textvariable=self.install_dir, width=50).pack()
        ttk.Button(self, text="Browse", command=self.browse).pack(pady=5)

        self.status = tk.StringVar(value="Waiting for location...")
        ttk.Label(self, textvariable=self.status).pack(pady=10)

        self.bar = ttk.Progressbar(self, length=420)
        self.bar.pack(pady=5)

        ttk.Button(self, text="Install", command=self.install).pack(pady=10)

    def browse(self):
