class Task:
    def __init__(self, id, name, xp_value):
        self.id = id
        self.name = name
        self.xp_value = xp_value


class Player:
    def __init__(self):
        self.total_xp = 0
        self.level = 1
        self.current_xp = 0
        self.next_level_xp = self.xp_required_for_level(1)

    def xp_required_for_level(self, level):
        # Exponential scaling starting at 50
        return int(50 * (1.5 ** (level - 1)))

    def gain_xp(self, amount):
        self.total_xp += amount
        self.recalculate()

    def recalculate(self):
        level = 1
        xp_remaining = self.total_xp

        while True:
            required = self.xp_required_for_level(level)
            if xp_remaining >= required:
                xp_remaining -= required
                level += 1
            else:
                break

        self.level = level
        self.current_xp = xp_remaining
        self.next_level_xp = self.xp_required_for_level(level)
