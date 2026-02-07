from datetime import datetime
from config import DIFFICULTY_MAP

def normalize(tasks):
    out = []
    for t in tasks:
        out.append({
            "id": t["id"],
            "name": t.get("title", "Task"),
            "completed": t.get("status") == 2,
            "xp": 25,
            "hp_penalty": 5
        })
    return out

def apply(player, tasks):
    today = datetime.now().date().isoformat()
    if player["last_update"] == today:
        return player

    if any(t["completed"] for t in tasks):
        player["streak"] += 1
    else:
        player["streak"] = 0

    for t in tasks:
        if t["completed"]:
            player["xp"] += t["xp"]
        else:
            player["hp"] -= t["hp_penalty"]

    player["last_update"] = today
    return player
