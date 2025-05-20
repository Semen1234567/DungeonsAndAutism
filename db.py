import sqlite3
import os

DB_PATH = "D:\\DungeonsAndAutism\\.data\\game.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER,
            chat_id INTEGER,
            nick TEXT,
            hp INTEGER DEFAULT 100,
            strength INTEGER DEFAULT 5,
            intellect INTEGER DEFAULT 5,
            agility INTEGER DEFAULT 5,
            is_alive BOOLEAN DEFAULT 1,
            PRIMARY KEY (user_id, chat_id)
        )
        """)

def get_player(user_id: int, chat_id: int):
    with get_db() as conn:
        cur = conn.execute("""
            SELECT nick, hp, strength, intellect, agility, is_alive
            FROM players WHERE user_id = ? AND chat_id = ?
        """, (user_id, chat_id))
        return cur.fetchone()

