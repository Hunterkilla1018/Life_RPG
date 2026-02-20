from datetime import datetime
from .save import load_player, save_player
from .progression import xp_required_for_rank
from .quest_manager import QuestManager


class Player:

    def __init__(self):
        self.data = load_player()
        self.daily_recovery()
        self.recalculate_rank()

        # Attach Quest Manager
        self.quest_manager = QuestManager(self)

    # -------------------------
    # Task Completion Entry Point
    # -------------------------

    def complete_task(self, task):
        """
        Unified task completion pipeline.
        """
        xp = task.xp_reward()

        # Apply XP normally (with quest notifications)
        self.gain_navigation_data(xp)

        # Notify quest that a task was completed
        self.quest_manager.notify_task_completed(task)

        self.save()

    # -------------------------
    # Progression
    # -------------------------

    def gain_navigation_data(self, amount):
        """
        Public XP pipeline (used for tasks).
        This notifies quests.
        """
        self._apply_navigation_data(amount)

        # Notify quests tracking navigation data
        self.quest_manager.notify_navigation_data(amount)

        self.save()

    def _apply_navigation_data(self, amount):
        """
        Internal XP application WITHOUT quest notifications.
        Used for quest rewards to avoid recursion.
        """
        self.data["total_navigation_data"] += amount
        self.data["credits"] += amount // 5
        self.data["warp_stability"] += 1

        self.recalculate_rank()

    def recalculate_rank(self):
        total = self.data["total_navigation_data"]

        rank = 1
        remaining = total

        while True:
            required = xp_required_for_rank(rank)
            if remaining >= required:
                remaining -= required
                rank += 1
            else:
                break

        self.data["rank"] = rank
        self.data["current_navigation_data"] = remaining
        self.data["next_rank_requirement"] = xp_required_for_rank(rank)

    # -------------------------
    # Failure System
    # -------------------------

    def fail_task(self, task):
        self.data["ship_integrity"] -= task.integrity_penalty()
        self.data["warp_stability"] = 0

        if self.data["ship_integrity"] <= 0:
            self.critical_failure()

        self.save()

    def critical_failure(self):
        self.data["credits"] = int(self.data["credits"] * 0.8)
        self.data["ship_integrity"] = 60
        self.data["warp_stability"] = 0
        self.data["last_emergency_repair_date"] = str(datetime.today().date())

    # -------------------------
    # Daily Recovery
    # -------------------------

    def daily_recovery(self):
        today = str(datetime.today().date())
        last = self.data.get("last_active_date")

        if last != today:
            self.data["ship_integrity"] = min(
                self.data["ship_integrity"] + 5,
                self.data["max_integrity"]
            )
            self.data["last_active_date"] = today
            self.save()

    # -------------------------
    # Dev Tools
    # -------------------------

    def dev_add_xp(self, amount):
        self.gain_navigation_data(amount)

    def dev_damage(self, amount):
        self.data["ship_integrity"] -= amount
        if self.data["ship_integrity"] <= 0:
            self.critical_failure()
        self.save()

    def dev_heal(self, amount):
        self.data["ship_integrity"] = min(
            self.data["ship_integrity"] + amount,
            self.data["max_integrity"]
        )
        self.save()

    def dev_add_credits(self, amount):
        self.data["credits"] += amount
        self.save()

    def dev_reset_integrity(self):
        self.data["ship_integrity"] = self.data["max_integrity"]
        self.save()

    # -------------------------
    # Save Wrapper
    # -------------------------

    def save(self):
        save_player(self.data)
