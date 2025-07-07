import sqlite3
import os

def init_db():
    if not os.path.exists("chat.db"):
        with sqlite3.connect("chat.db") as conn:
            with open("schema.sql", "r") as f:
                conn.executescript(f.read())

def get_db():
    return sqlite3.connect("chat.db")
