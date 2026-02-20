class Objective:
    def __init__(self, id, type, target):
        self.id = id
        self.type = type
        self.target = target
        self.current = 0
        self.completed = False

    def notify_task_completed(self, task):
        if self.completed:
            return

        if self.type == "complete_task":
            self.current += 1
            self._check_complete()

    def notify_navigation_data(self, amount):
        if self.completed:
            return

        if self.type == "accumulate_navigation_data":
            self.current += amount
            self._check_complete()

    def _check_complete(self):
        if self.current >= self.target:
            self.current = self.target  # 🔥 clamp
            self.completed = True

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "target": self.target,
            "current": self.current,
            "completed": self.completed
        }

    @classmethod
    def from_dict(cls, data):
        obj = cls(data["id"], data["type"], data["target"])
        obj.current = data.get("current", 0)
        obj.completed = data.get("completed", False)
        return obj
