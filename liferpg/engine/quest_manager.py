from .quest import Quest
from .objective import Objective


class QuestManager:
    def __init__(self, player):
        self.player = player
        self.quests = {}

        self.load_or_initialize()

    # -------------------------
    # Load / Init
    # -------------------------

    def load_or_initialize(self):
        saved = self.player.data.get("quests", {})

        if not saved:
            self.initialize_default_quests()
        else:
            for qid, qdata in saved.items():
                self.quests[qid] = Quest.from_dict(qdata)

    def initialize_default_quests(self):
        quest = Quest(
            id="ship_stabilization",
            name="Ship Stabilization Protocol",
            description="Complete 3 tasks and earn 100 navigation data.",
            objectives=[
                Objective("obj_tasks", "complete_task", 3),
                Objective("obj_nav", "accumulate_navigation_data", 100)
            ],
            rewards={
                "navigation_data": 150,
                "credits": 100
            }
        )

        self.quests[quest.id] = quest
        self.save()

    # -------------------------
    # Notifications
    # -------------------------

    def notify_task_completed(self, task):
        for quest in self.quests.values():
            quest.notify_task_completed(task)

        self.save()

    def notify_navigation_data(self, amount):
        for quest in self.quests.values():
            quest.notify_navigation_data(amount)

        self.apply_completed_rewards()
        self.save()

    # -------------------------
    # Reward Application
    # -------------------------

    def apply_completed_rewards(self):
        for quest in self.quests.values():
            if quest.is_completed() and not quest.rewards.get("_applied", False):

                rewards = quest.rewards

                # Apply XP WITHOUT triggering quest notifications again
                if "navigation_data" in rewards:
                    self.player._apply_navigation_data(
                        rewards["navigation_data"]
                    )

                if "credits" in rewards:
                    self.player.data["credits"] += rewards["credits"]

                quest.rewards["_applied"] = True

    # -------------------------
    # Save
    # -------------------------

    def save(self):
        self.player.data["quests"] = {
            qid: quest.to_dict() for qid, quest in self.quests.items()
        }
        self.player.save()
