from flask import Flask, request, session, jsonify
from flask_cors import CORS
from auth import create_user, verify_user, is_strong_password # Import is_strong_password
from chatbot import ask_groq
from db import init_db, get_db
import datetime

app = Flask(__name__)
app.secret_key = "supercutesecret"
CORS(app, supports_credentials=True)

init_db()

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."})

    if not is_strong_password(password):
        return jsonify({"success": False, "message": "Password does not meet strength requirements: minimum 8 characters, at least one uppercase letter, one lowercase letter, one number, and one special character."})
    
    if create_user(username, password):
        return jsonify({"success": True, "message": "Signup successful! You can now log in."})
    return jsonify({"success": False, "message": "Username already exists."})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    remember_me = data.get("remember_me", False) # Get remember_me status

    uid = verify_user(username, password)
    if uid:
        session["user_id"] = uid
        if remember_me:
            session.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(hours=24) # Session lasts 24 hours
        else:
            session.permanent = False # Session ends when browser closes
        return jsonify({"success": True, "message": "Login successful!"})
    return jsonify({"success": False, "message": "Invalid credentials."})

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"success": True, "message": "Logged out successfully."})

@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"success": False, "response": "Please log in first."})
    
    data = request.json
    msg = data["message"]
    chat_history = data.get("history", []) # Get chat history from the request

    # Construct messages for Groq API, including previous conversation
    # The format should be [{"role": "user", "content": "..."}] and [{"role": "assistant", "content": "..."}]
    messages_for_groq = []
    for turn in chat_history:
        if turn[0]: # User message
            messages_for_groq.append({"role": "user", "content": turn[0]})
        if turn[1]: # Bot response
            messages_for_groq.append({"role": "assistant", "content": turn[1]})
    messages_for_groq.append({"role": "user", "content": msg}) # Add the current message

    reply = ask_groq(messages_for_groq) # Pass the full history to ask_groq

    db = get_db()
    db.execute("INSERT INTO messages (user_id, message, response) VALUES (?, ?, ?)",
               (session["user_id"], msg, reply))
    db.commit()
    return jsonify({"success": True, "response": reply})
@app.route("/check_login_status", methods=["GET"])
def check_login_status():
    if "user_id" in session:
        return jsonify({"logged_in": True})
    return jsonify({"logged_in": False})

@app.route("/get_chat_history", methods=["GET"])
def get_chat_history():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."})
    
    user_id = session["user_id"]
    db = get_db()
    messages = db.execute("SELECT message, response FROM messages WHERE user_id = ? ORDER BY timestamp", (user_id,)).fetchall()
    
    # Gradio's Chatbot expects history as a list of lists: [[user_msg, bot_reply], ...]
    history = [[msg[0], msg[1]] for msg in messages]
    return jsonify({"success": True, "history": history})

if __name__ == "__main__":
    app.run(debug=True)