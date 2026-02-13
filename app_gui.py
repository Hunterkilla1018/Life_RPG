import tkinter as tk
from tkinter import ttk
from game_logic import Player, Task


class LifeRPGApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("LifeRPG v0.0.2")
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

        self.bind("<F12>", self.toggle_console)

    # =============================
    # UI BUILD
    # =============================

    def build_ui(self):

        self.rank_label = ttk.Label(self, text="")
        self.rank_label.pack(pady=5)

        self.nav_label = ttk.Label(self, text="")
        self.nav_label.pack(pady=5)

        self.nav_progress = ttk.Progressbar(self, length=600)
        self.nav_progress.pack(pady=5)

        self.integrity_label = ttk.Label(self, text="")
        self.integrity_label.pack(pady=5)

        self.integrity_progress = ttk.Progressbar(self, length=600)
        self.integrity_progress.pack(pady=5)

        self.economy_label = ttk.Label(self, text="")
        self.economy_label.pack(pady=5)

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=10)

        self.task_frame = ttk.Frame(self)
        self.task_frame.pack(pady=10)

        for task in self.tasks:
            frame = ttk.Frame(self.task_frame)
            frame.pack(fill="x", pady=3)

            ttk.Label(
                frame,
                text=f"{task.name} ({task.difficulty.upper()})"
            ).pack(side="left", padx=5)

            ttk.Button(
                frame,
                text="Complete",
                command=lambda t=task: self.complete_task(t)
            ).pack(side="right", padx=5)

            ttk.Button(
                frame,
                text="Fail",
                command=lambda t=task: self.fail_task(t)
            ).pack(side="right")

        # =============================
        # DEV CONSOLE (HIDDEN)
        # =============================

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

    # =============================
    # TASK ACTIONS
    # =============================

    def complete_task(self, task):
        self.player.gain_navigation_data(task.xp_reward())
        self.refresh_ui()

    def fail_task(self, task):
        self.player.fail_task(task)
        self.refresh_ui()

    # =============================
    # DEV CONSOLE
    # =============================

    def toggle_console(self, event=None):
        if self.console_visible:
            self.console_frame.pack_forget()
            self.console_visible = False
        else:
            self.console_frame.pack(fill="x", pady=10)
            self.console_visible = True

    def execute_command(self, event=None):
        cmd = self.console_input.get().strip()
        self.console_input.delete(0, "end")

        try:
            parts = cmd.split()

            if parts[0] == "status":
                self.print_console(str(self.player.dev_status()))

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
                self.player.critical_ship_failure()

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

    # =============================
    # UI REFRESH
    # =============================

    def refresh_ui(self):
        data = self.player.data

        self.rank_label.config(text=f"Rank: {data['rank']}")

        self.nav_label.config(
            text=f"Navigation Data: "
                 f"{data['current_navigation_data']} GB / "
                 f"{data['next_rank_requirement']} GB"
        )

        self.nav_progress["maximum"] = data["next_rank_requirement"]
        self.nav_progress["value"] = data["current_navigation_data"]

        self.integrity_label.config(
            text=f"Ship Integrity: {data['ship_integrity']} / {data['max_integrity']}"
        )

        self.integrity_progress["maximum"] = data["max_integrity"]
        self.integrity_progress["value"] = data["ship_integrity"]

        self.economy_label.config(
            text=f"Credits: {data['credits']} | Warp Stability: {data['warp_stability']}"
        )


def run_ui():
    app = LifeRPGApp()
    app.mainloop()
