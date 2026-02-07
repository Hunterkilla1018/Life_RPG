APP_NAME = "Life RPG"

SAVE_DIR = "life_rpg_save"

DIFFICULTY_MAP = {
    "easy": {"xp": 10, "hp_penalty": 0},
    "medium": {"xp": 25, "hp_penalty": 5},
    "hard": {"xp": 50, "hp_penalty": 10},
    "boss": {"xp": 100, "hp_penalty": 25}
}

DEFAULT_PLAYER = {
    "level": 1,
    "xp": 0,
    "xp_to_next": 100,
    "hp": 100,
    "max_hp": 100,
    "gold": 0,
    "streak": 0,
    "last_update": None
}
