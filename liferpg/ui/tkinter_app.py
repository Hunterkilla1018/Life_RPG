import tkinter as tk
from tkinter import ttk
from liferpg.engine.player import Player
from liferpg.engine.task import Task


class LifeRPGApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("LifeRPG v0.0.3")
        self.geometry("750x600")

        self.player = Player()
        self.console_visible = False

        self.tasks = [
            Task(1, "Calibrate Navigation Systems", "easy"),
            Task(2, "Repair External Hull Plating", "medium"),
            Task(3, "Asteroid Field Maneuver", "hard"),
            Task(4, "Deep Space Boss Encounter", "boss"),
        ]

        self.build_ui()
        self.refresh_ui()

        # 🔥 Global F12 binding
        self.bind_all("<F12>", self.toggle_console)
        self.focus_set()

    # -------------------------
    # UI
    # -------------------------

    def build_ui(self):
        self.rank_label = ttk.Label(self, text="")
        self.rank_label.pack(pady=5)

        self.nav_label = ttk.Label(self, text="")
        self.nav_label.pack(pady=5)

        self.progress = ttk.Progressbar(self, length=500)
        self.progress.pack(pady=5)

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=10)

        self.task_frame = ttk.Frame(self)
        self.task_frame.pack(pady=10)

        for task in self.tasks:
            frame = ttk.Frame(self.task_frame)
            frame.pack(fill="x", pady=3)

            ttk.Label(frame, text=f"{task.name} ({task.difficulty})").pack(side="left")

            ttk.Button(
                frame,
                text="Complete",
                command=lambda t=task: self.complete_task(t)
            ).pack(side="right")

        # -------------------------
        # DEV CONSOLE
        # -------------------------

        self.console_frame = ttk.Frame(self)

        self.console_output = tk.Text(
            self.console_frame,
            height=8,
            bg="#111",
            fg="#00ff88"
        )
        self.console_output.pack(fill="x")

        self.console_input = ttk.Entry(self.console_frame)
        self.console_input.pack(fill="x")
        self.console_input.bind("<Return>", self.execute_command)

    # -------------------------
    # Task Actions
    # -------------------------

    def complete_task(self, task):
        self.player.gain_navigation_data(task.xp_reward())
        self.refresh_ui()

    # -------------------------
    # Console
    # -------------------------

    def toggle_console(self, event=None):
        if self.console_visible:
            self.console_frame.pack_forget()
            self.console_visible = False
        else:
            self.console_frame.pack(fill="x", pady=10)
            self.console_visible = True

        return "break"

    def execute_command(self, event=None):
        cmd = self.console_input.get().strip()
        self.console_input.delete(0, "end")

        try:
            parts = cmd.split()

            if parts[0] == "status":
                self.print_console(str(self.player.data))

            elif parts[0] == "add_xp":
                self.player.dev_add_xp(int(parts[1]))

            elif parts[0] == "damage":
                self.player.dev_damage(int(parts[1]))

            elif parts[0] == "heal":
                self.player.dev_heal(int(parts[1]))

            elif parts[0] == "add_credits":
                self.player.dev_add_credits(int(parts[1]))

            elif parts[0] == "reset_integrity":
                self.player.dev_reset_integrity()

            elif parts[0] == "force_failure":
                self.player.critical_failure()

            elif parts[0] == "save":
                self.player.save()

            else:
                self.print_console("Unknown command")

        except Exception as e:
            self.print_console(f"Error: {e}")

        self.refresh_ui()

    def print_console(self, text):
        self.console_output.insert("end", text + "\n")
        self.console_output.see("end")

    # -------------------------
    # UI Refresh
    # -------------------------

    def refresh_ui(self):
        data = self.player.data

        self.rank_label.config(text=f"Rank: {data['rank']}")
        self.nav_label.config(
            text=f"{data['current_navigation_data']} / {data['next_rank_requirement']}"
        )

        self.progress["maximum"] = data["next_rank_requirement"]
        self.progress["value"] = data["current_navigation_data"]
