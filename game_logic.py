from datetime import datetime
from storage import load_player, save_player


# ============================================================
# TASK
# ============================================================

class Task:
    def __init__(self, id, name, difficulty="easy"):
        self.id = id
        self.name = name
        self.difficulty = difficulty

    def xp_reward(self):
        table = {
            "easy": 10,
            "medium": 25,
            "hard": 50,
            "boss": 100
        }
        return table.get(self.difficulty, 10)

    def integrity_penalty(self):
        table = {
            "easy": 2,
            "medium": 5,
            "hard": 10,
            "boss": 20
        }
        return table.get(self.difficulty, 2)


# ============================================================
# PLAYER
# ============================================================

class Player:
    def __init__(self):
        self.data = self._load_and_migrate()
        self.daily_recovery_check()
        self.recalculate_rank()

    # ============================================================
    # SAVE MIGRATION (PATCH SAFE)
    # ============================================================

    def _load_and_migrate(self):
        old = load_player()

        migrated = {
            "rank": old.get("rank", old.get("level", 1)),

            "total_navigation_data": old.get(
                "total_navigation_data",
                old.get("xp", 0)
            ),

            "current_navigation_data": 0,
            "next_rank_requirement": 50,

            "ship_integrity": old.get(
                "ship_integrity",
                old.get("hp", 100)
            ),

            "max_integrity": old.get("max_integrity", 100),

            "credits": old.get(
                "credits",
                old.get("gold", 0)
            ),

            "warp_stability": old.get(
                "warp_stability",
                old.get("streak", 0)
            ),

            "inventory": old.get("inventory", {}),

            "last_active_date": old.get("last_active_date"),
            "last_emergency_repair_date": old.get("last_emergency_repair_date")
        }

        return migrated

    # ============================================================
    # RANK / NAVIGATION DATA SYSTEM
    # ============================================================

    def xp_required_for_rank(self, rank):
        return int(50 * (1.5 ** (rank - 1)))

    def gain_navigation_data(self, amount):
        self.data["total_navigation_data"] += amount

        # Earn credits passively
        self.data["credits"] += amount // 5

        # Increase streak
        self.data["warp_stability"] += 1

        self.recalculate_rank()
        self.save()

    def recalculate_rank(self):
        total = self.data["total_navigation_data"]

        rank = 1
        remaining = total

        while True:
            required = self.xp_required_for_rank(rank)
            if remaining >= required:
                remaining -= required
                rank += 1
            else:
                break

        self.data["rank"] = rank
        self.data["current_navigation_data"] = remaining
        self.data["next_rank_requirement"] = self.xp_required_for_rank(rank)

    # ============================================================
    # FAILURE SYSTEM
    # ============================================================

    def fail_task(self, task):
        penalty = task.integrity_penalty()

        self.data["ship_integrity"] -= penalty

        # Reset streak on failure
        self.data["warp_stability"] = 0

        if self.data["ship_integrity"] <= 0:
            self.critical_ship_failure()

        self.save()

    def critical_ship_failure(self):
        # Lose 20% credits
        self.data["credits"] = int(self.data["credits"] * 0.8)

        # Restore integrity to 60%
        self.data["ship_integrity"] = 60

        # Reset streak
        self.data["warp_stability"] = 0

        self.data["last_emergency_repair_date"] = str(datetime.today().date())

    # ============================================================
    # DAILY RECOVERY SYSTEM
    # ============================================================

    def daily_recovery_check(self):
        today = str(datetime.today().date())
        last = self.data.get("last_active_date")

        if last != today:
            self.data["ship_integrity"] = min(
                self.data["ship_integrity"] + 5,
                self.data["max_integrity"]
            )
            self.data["last_active_date"] = today
            self.save()

    # ============================================================
    # DEV CONSOLE UTILITIES
    # ============================================================

    def dev_status(self):
        return self.data

    def dev_add_xp(self, amount):
        self.gain_navigation_data(amount)

    def dev_damage(self, amount):
        self.data["ship_integrity"] -= amount
        if self.data["ship_integrity"] <= 0:
            self.critical_ship_failure()
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

    # ============================================================
    # SAVE
    # ============================================================

    def save(self):
        save_player(self.data)
