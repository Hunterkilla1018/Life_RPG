from .objective import Objective


class Quest:
    def __init__(self, id, name, description, objectives, rewards):
        self.id = id
        self.name = name
        self.description = description
        self.objectives = objectives  # list of Objective
        self.rewards = rewards  # dict
        self.status = "active"  # locked / active / completed

    def notify_task_completed(self, task):
        if self.status != "active":
            return

        for obj in self.objectives:
            obj.notify_task_completed(task)

        self.check_completion()

    def notify_navigation_data(self, amount):
        if self.status != "active":
            return

        for obj in self.objectives:
            obj.notify_navigation_data(amount)

        self.check_completion()

    def check_completion(self):
        if all(obj.completed for obj in self.objectives):
            self.status = "completed"

    def is_completed(self):
        return self.status == "completed"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "objectives": [o.to_dict() for o in self.objectives],
            "rewards": self.rewards
        }

    @classmethod
    def from_dict(cls, data):
        objectives = [Objective.from_dict(o) for o in data["objectives"]]
        quest = cls(
            data["id"],
            data["name"],
            data["description"],
            objectives,
            data["rewards"]
        )
        quest.status = data.get("status", "active")
        return quest
