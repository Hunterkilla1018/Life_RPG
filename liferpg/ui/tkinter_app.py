import tkinter as tk
from tkinter import ttk
import json

from liferpg.engine.player import Player
from liferpg.engine.task import Task


class LifeRPGApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("LifeRPG v0.0.4")
        self.geometry("900x750")
        self.configure(bg="#0f1117")

        self.player = Player()
        self.console_visible = False
        self.dev_mode = False

        self.tasks = [
            Task(1, "Calibrate Navigation Systems", "easy"),
            Task(2, "Repair External Hull Plating", "medium"),
            Task(3, "Asteroid Field Maneuver", "hard"),
            Task(4, "Deep Space Boss Encounter", "boss"),
        ]

        self.build_ui()
        self.refresh_ui()

        self.bind_all("<F12>", self.toggle_console)

    # ======================================================
    # UI BUILD
    # ======================================================

    def build_ui(self):

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Header.TLabel",
                        background="#0f1117",
                        foreground="#00d9ff",
                        font=("Consolas", 14, "bold"))

        style.configure("Normal.TLabel",
                        background="#0f1117",
                        foreground="#c7f0ff",
                        font=("Consolas", 10))

        style.configure("Active.TLabel",
                        background="#0f1117",
                        foreground="#ffcc00",
                        font=("Consolas", 10, "bold"))

        style.configure("Completed.TLabel",
                        background="#0f1117",
                        foreground="#00ff88",
                        font=("Consolas", 10, "bold"))

        # =========================
        # HEADER BAR
        # =========================

        self.header = tk.Frame(self, bg="#0f1117")
        self.header.pack(fill="x", pady=10)

        self.rank_label = ttk.Label(self.header, style="Header.TLabel")
        self.rank_label.pack(side="left", padx=20)

        self.nav_label = ttk.Label(self.header, style="Normal.TLabel")
        self.nav_label.pack(side="left")

        self.settings_btn = ttk.Button(
            self.header,
            text="⚙",
            width=3,
            command=self.open_settings
        )
        self.settings_btn.pack(side="right", padx=20)

        self.progress = ttk.Progressbar(self, length=700)
        self.progress.pack(pady=5)

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=15)

        # =========================
        # DEV OVERLAY
        # =========================

        self.dev_overlay = tk.Frame(self, bg="#1a1f2b")
        # initially hidden

        # =========================
        # TASK PANEL
        # =========================

        self.task_frame = ttk.Frame(self)
        self.task_frame.pack(pady=10)

        for task in self.tasks:
            frame = ttk.Frame(self.task_frame)
            frame.pack(fill="x", pady=4)

            ttk.Label(frame,
                      text=f"{task.name} ({task.difficulty})",
                      style="Normal.TLabel").pack(side="left")

            ttk.Button(
                frame,
                text="Complete",
                command=lambda t=task: self.complete_task(t)
            ).pack(side="right")

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=20)

        # =========================
        # MISSION CONTROL PANEL
        # =========================

        self.quest_container = tk.Frame(
            self,
            bg="#0f1117",
            highlightbackground="#00d9ff",
            highlightthickness=1
        )
        self.quest_container.pack(fill="x", padx=40, pady=10)

        ttk.Label(self.quest_container,
                  text="MISSION CONTROL",
                  style="Header.TLabel").pack(anchor="w", padx=10, pady=5)

        self.quest_content = tk.Frame(self.quest_container, bg="#0f1117")
        self.quest_content.pack(fill="x", padx=15, pady=5)

        # =========================
        # DEV CONSOLE
        # =========================

        self.console_frame = ttk.Frame(self)

        scrollbar = ttk.Scrollbar(self.console_frame)
        scrollbar.pack(side="right", fill="y")

        self.console_output = tk.Text(
            self.console_frame,
            height=10,
            bg="#111",
            fg="#00ff88",
            insertbackground="#00ff88",
            wrap="word",
            yscrollcommand=scrollbar.set
        )
        self.console_output.pack(fill="both", expand=True)
        scrollbar.config(command=self.console_output.yview)

        self.console_input = ttk.Entry(self.console_frame)
        self.console_input.pack(fill="x")
        self.console_input.bind("<Return>", self.execute_command)

    # ======================================================
    # SETTINGS WINDOW
    # ======================================================

    def open_settings(self):
        win = tk.Toplevel(self)
        win.title("Settings")
        win.geometry("300x200")
        win.configure(bg="#0f1117")

        dev_var = tk.BooleanVar(value=self.dev_mode)

        def toggle_dev():
            self.dev_mode = dev_var.get()
            self.update_dev_overlay()

        ttk.Checkbutton(
            win,
            text="Enable Developer Mode",
            variable=dev_var,
            command=toggle_dev
        ).pack(pady=20)

    # ======================================================
    # DEV OVERLAY LOGIC
    # ======================================================

    def update_dev_overlay(self):
        for widget in self.dev_overlay.winfo_children():
            widget.destroy()

        if self.dev_mode:
            self.dev_overlay.pack(fill="x")

            ttk.Label(
                self.dev_overlay,
                text="DEVELOPER OVERLAY",
                foreground="#ff5555",
                background="#1a1f2b"
            ).pack(side="left", padx=10)

            ttk.Button(
                self.dev_overlay,
                text="+100 XP",
                command=lambda: self.player.dev_add_xp(100)
            ).pack(side="left", padx=5)

            ttk.Button(
                self.dev_overlay,
                text="+500 Credits",
                command=lambda: self.player.dev_add_credits(500)
            ).pack(side="left", padx=5)

            ttk.Button(
                self.dev_overlay,
                text="Force Failure",
                command=self.player.critical_failure
            ).pack(side="left", padx=5)

        else:
            self.dev_overlay.pack_forget()
            self.console_frame.pack_forget()

    # ======================================================
    # TASK ACTION
    # ======================================================

    def complete_task(self, task):
        self.player.complete_task(task)
        self.refresh_ui()

    # ======================================================
    # QUEST RENDERING
    # ======================================================

    def render_quests(self):
        for widget in self.quest_content.winfo_children():
            widget.destroy()

        for quest in self.player.quest_manager.quests.values():

            ttk.Label(
                self.quest_content,
                text=quest.name,
                style="Header.TLabel"
            ).pack(anchor="w", pady=(5, 2))

            for obj in quest.objectives:
                percent = obj.current / obj.target
                bar = "█" * int(percent * 10)
                bar += "░" * (10 - len(bar))

                line = f"▸ {obj.type.replace('_',' ').title():<25} {obj.current}/{obj.target:<5} {bar}"

                ttk.Label(
                    self.quest_content,
                    text=line,
                    style="Normal.TLabel"
                ).pack(anchor="w")

            style_name = "Completed.TLabel" if quest.status == "completed" else "Active.TLabel"

            ttk.Label(
                self.quest_content,
                text=f"STATUS: {quest.status.upper()}",
                style=style_name
            ).pack(anchor="w", pady=(5, 5))

            rewards = " | ".join(
                [f"+{v} {k.upper()}" for k, v in quest.rewards.items()
                 if not k.startswith("_")]
            )

            ttk.Label(
                self.quest_content,
                text=f"REWARD: {rewards}",
                style="Normal.TLabel"
            ).pack(anchor="w", pady=(0, 10))

    # ======================================================
    # DEV CONSOLE
    # ======================================================

    def toggle_console(self, event=None):
        if not self.dev_mode:
            return "break"

        if self.console_visible:
            self.console_frame.pack_forget()
            self.console_visible = False
        else:
            self.console_frame.pack(fill="both", expand=True, pady=10)
            self.console_visible = True

        return "break"

    def execute_command(self, event=None):
        cmd = self.console_input.get().strip()
        self.console_input.delete(0, "end")

        try:
            parts = cmd.split()
            if parts and parts[0] == "add_xp":
                self.player.dev_add_xp(int(parts[1]))
            else:
                self.print_console("Unknown command")

        except Exception as e:
            self.print_console(f"Error: {e}")

        self.refresh_ui()

    def print_console(self, text):
        self.console_output.insert("end", text + "\n")
        self.console_output.see("end")

    # ======================================================
    # REFRESH
    # ======================================================

    def refresh_ui(self):
        data = self.player.data

        self.rank_label.config(text=f"RANK: {data['rank']}")
        self.nav_label.config(
            text=f"   NAVIGATION DATA: {data['current_navigation_data']} / {data['next_rank_requirement']}"
        )

        self.progress["maximum"] = data["next_rank_requirement"]
        self.progress["value"] = data["current_navigation_data"]

        self.render_quests()
