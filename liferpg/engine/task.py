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
