import bcrypt
from db import get_db
import re

def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

def create_user(username, password):
    if not is_strong_password(password):
        return False # Password does not meet strength requirements

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    db = get_db()
    try:
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        db.commit()
        return True
    except:
        return False

def verify_user(username, password):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user and bcrypt.checkpw(password.encode(), user[2]):
        return user[0]
    return None