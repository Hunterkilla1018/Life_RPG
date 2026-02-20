import os
import json
from .schema import DEFAULT_PLAYER

SAVE_DIR = "life_rpg_save"
PLAYER_FILE = os.path.join(SAVE_DIR, "player.json")

os.makedirs(SAVE_DIR, exist_ok=True)


def load_player():
    if not os.path.exists(PLAYER_FILE):
        return DEFAULT_PLAYER.copy()

    with open(PLAYER_FILE, "r") as f:
        data = json.load(f)

    # basic migration safety
    for key, value in DEFAULT_PLAYER.items():
        if key not in data:
            data[key] = value

    return data


def save_player(data):
    with open(PLAYER_FILE, "w") as f:
        json.dump(data, f, indent=4)
