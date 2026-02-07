import requests

BASE = "https://api.ticktick.com/open/v1"

def fetch_tasks(token):
    r = requests.post(
        f"{BASE}/task/query",
        headers={"Authorization": f"Bearer {token}"},
        json={}
    )
    if r.status_code != 200:
        raise Exception(r.text)
    return r.json().get("tasks", [])
