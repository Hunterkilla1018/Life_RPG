import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def write_file(path, content):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

def main():
    os.makedirs("life_rpg_save", exist_ok=True)
    os.makedirs(".github/workflows", exist_ok=True)

    write_file("config.py", """APP_NAME = "Life RPG"

SAVE_DIR = "life_rpg_save"

DIFFICULTY_MAP = {
    "easy": {"xp": 10, "hp_penalty": 0},
    "medium": {"xp": 25, "hp_penalty": 5},
    "hard": {"xp": 50, "hp_penalty": 10},
    "boss": {"xp": 100, "hp_penalty": 25}
}

DEFAULT_PLAYER = {
    "level": 1,
    "xp": 0,
    "xp_to_next": 100,
    "hp": 100,
    "max_hp": 100,
    "gold": 0,
    "streak": 0,
    "last_update": None
}
""")

    write_file("storage.py", """import os, json, base64, hashlib
from cryptography.fernet import Fernet
from config import SAVE_DIR, DEFAULT_PLAYER

os.makedirs(SAVE_DIR, exist_ok=True)

TOKEN_FILE = os.path.join(SAVE_DIR, "token.bin")
PLAYER_FILE = os.path.join(SAVE_DIR, "player.json")

def _key():
    return base64.urlsafe_b64encode(
        hashlib.sha256(os.getlogin().encode()).digest()
    )

_fernet = Fernet(_key())

def save_token(token):
    with open(TOKEN_FILE, "wb") as f:
        f.write(_fernet.encrypt(token.encode()))

def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    return _fernet.decrypt(open(TOKEN_FILE, "rb").read()).decode()

def load_player():
    if not os.path.exists(PLAYER_FILE):
        return DEFAULT_PLAYER.copy()
    return json.load(open(PLAYER_FILE))

def save_player(p):
    json.dump(p, open(PLAYER_FILE, "w"), indent=4)
""")

    write_file("api_ticktick.py", """import requests

BASE = "https://api.ticktick.com/open/v1"

def fetch_tasks(token):
    r = requests.post(
        f"{BASE}/task/query",
        headers={"Authorization": f"Bearer {token}"},
        json={}
    )
    if r.status_code != 200:
        raise Exception(r.text)
    return r.json().get("tasks", [])
""")

    write_file("game_logic.py", """from datetime import datetime
from config import DIFFICULTY_MAP

def normalize(tasks):
    out = []
    for t in tasks:
        out.append({
            "id": t["id"],
            "name": t.get("title", "Task"),
            "completed": t.get("status") == 2,
            "xp": 25,
            "hp_penalty": 5
        })
    return out

def apply(player, tasks):
    today = datetime.now().date().isoformat()
    if player["last_update"] == today:
        return player

    if any(t["completed"] for t in tasks):
        player["streak"] += 1
    else:
        player["streak"] = 0

    for t in tasks:
        if t["completed"]:
            player["xp"] += t["xp"]
        else:
            player["hp"] -= t["hp_penalty"]

    player["last_update"] = today
    return player
""")

    write_file("app_gui.py", """import tkinter as tk
from tkinter import ttk
from storage import load_token, load_player, save_player
from api_ticktick import fetch_tasks
from game_logic import normalize, apply

class LifeRPGApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Life RPG")
        self.geometry("600x400")

        self.label = ttk.Label(self, text="Life RPG Loaded")
        self.label.pack(pady=20)

        self.refresh()

    def refresh(self):
        token = load_token()
        if not token:
            return
        tasks = normalize(fetch_tasks(token))
        player = apply(load_player(), tasks)
        save_player(player)
""")

    write_file("main.py", """from app_gui import LifeRPGApp
LifeRPGApp().mainloop()
""")

    write_file("version.txt", "1.0\n")

    write_file(".github/workflows/build.yml", """name: Build Life RPG

on:
  push:
    tags:
      - "v*"

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install pyinstaller cryptography requests
      - run: pyinstaller --onefile --noconsole bootstrap.py
      - uses: softprops/action-gh-release@v2
        with:
          files: dist/bootstrap.exe
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
""")

    print("✅ Initial project files created. Ready for git push.")

if __name__ == "__main__":
    main()
