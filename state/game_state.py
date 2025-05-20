from config.prompts import prompt_by
from typing import Dict

class Player:
    def __init__(self, user_id: int, name: str, nick: str):
        self.id, self.name, self.nick = user_id, name, nick
        self.is_alive = True

class Room:
    def __init__(self, mode: str, lang: str, admin: int):
        self.mode = mode
        self.lang = lang
        self.admin = admin
        self.round = 1
        self.actions = {}
        self.players = {}
        self.system_prompt = prompt_by(mode, lang)
        self.chat = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": "Приветствие: Вы в мире фентези"},
        ]

rooms: Dict[int, Room] = {}
langs: Dict[int, str] = {}

def get_room(cid: int) -> Room:
    if cid not in rooms:
        rooms[cid] = Room("fantasy", langs.get(cid, "ru"), 0)
    return rooms[cid]
