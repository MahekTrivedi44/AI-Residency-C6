import bcrypt
from db import get_db

def create_user(username, password):
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
