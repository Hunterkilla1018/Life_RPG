import tkinter as tk
from tkinter import ttk
from game_logic import Player, Task


class LifeRPGApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("lifeRPG v0.0.1")
        self.geometry("600x400")

        self.player = Player()

        # High XP for testing so we can scale past level 3
        self.tasks = [
            Task(1, "Test Task 1", 100),
            Task(2, "Test Task 2", 150),
            Task(3, "Test Task 3", 250),
        ]

        self.level_label = ttk.Label(self, text="")
        self.level_label.pack(pady=5)

        self.xp_label = ttk.Label(self, text="")
        self.xp_label.pack(pady=5)

        self.progress = ttk.Progressbar(self, length=400)
        self.progress.pack(pady=10)

        self.task_frame = ttk.Frame(self)
        self.task_frame.pack(pady=10)

        self.render_tasks()
        self.refresh_ui()

    def render_tasks(self):
        for task in self.tasks:
            btn = ttk.Button(
                self.task_frame,
                text=f"{task.name} (+{task.xp_value} XP)",
                command=lambda t=task: self.complete_task(t)
            )
            btn.pack(pady=2)

    def complete_task(self, task):
        # Repeatable for testing purposes
        self.player.gain_xp(task.xp_value)
        self.refresh_ui()

    def refresh_ui(self):
        self.level_label.config(text=f"Level: {self.player.level}")

        self.xp_label.config(
            text=f"XP: {self.player.current_xp} / {self.player.next_level_xp}"
        )

        self.progress["maximum"] = self.player.next_level_xp
        self.progress["value"] = self.player.current_xp


def run_ui():
    app = LifeRPGApp()
    app.mainloop()
