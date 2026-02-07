import os, json, base64, hashlib
from cryptography.fernet import Fernet
from config import SAVE_DIR, DEFAULT_PLAYER

os.makedirs(SAVE_DIR, exist_ok=True)

TOKEN_FILE = os.path.join(SAVE_DIR, "token.bin")
PLAYER_FILE = os.path.join(SAVE_DIR, "player.json")

def _key():
    return base64.urlsafe_b64encode(
        hashlib.sha256(os.getlogin().encode()).digest()
    )

_fernet = Fernet(_key())

def save_token(token):
    with open(TOKEN_FILE, "wb") as f:
        f.write(_fernet.encrypt(token.encode()))

def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    return _fernet.decrypt(open(TOKEN_FILE, "rb").read()).decode()

def load_player():
    if not os.path.exists(PLAYER_FILE):
        return DEFAULT_PLAYER.copy()
    return json.load(open(PLAYER_FILE))

def save_player(p):
    json.dump(p, open(PLAYER_FILE, "w"), indent=4)
