import tkinter as tk
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
