import sqlite3
import os
import bcrypt
import requests
from flask import Flask, request, session, jsonify, g
from flask_cors import CORS
from datetime import datetime, timedelta

# --- Configuration ---
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = "supercutesecret" # IMPORTANT: Use a strong, random secret key in production!
CORS(app, supports_credentials=True)

# --- Database Functions ---
DATABASE = "chat.db"

def init_db():
    if not os.path.exists(DATABASE):
        with sqlite3.connect(DATABASE) as conn:
            with open("schema.sql", "r") as f:
                conn.executescript(f.read())

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row # This allows accessing columns by name
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# Initialize the database when the app starts
init_db()

# --- Auth Functions ---
def create_user(username, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    db = get_db()
    try:
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        db.commit()
        return True
    except sqlite3.IntegrityError: # Catch if username already exists
        return False
    except Exception as e:
        print(f"Error creating user: {e}")
        db.rollback()
        return False

def verify_user(username, password):
    db = get_db()
    user = db.execute("SELECT id, password FROM users WHERE username = ?", (username,)).fetchone()
    if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]): # user[1] is the password column
        return user["id"] # Return user ID
    return None

# --- Chatbot Function ---
def ask_groq(messages_list):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages_list
    }
    try:
        response = requests.post(GROQ_ENDPOINT, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return f"Error from AI: {e.response.text}"
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
        return "Failed to connect to the AI service. Please check your internet connection or API endpoint."
    except requests.exceptions.Timeout:
        print("Timeout Error: AI service did not respond in time.")
        return "AI service took too long to respond."
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return f"An error occurred with the AI request: {e}"
    except KeyError:
        print(f"Unexpected API response format: {response.json()}")
        return "Received unexpected response from AI. Please try again."


# --- Helper for Conversation Management ---
def get_or_create_default_conversation(user_id):
    db = get_db()
    
    if "current_conversation_id" in session and session["current_conversation_id"]:
        conv = db.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?",
                          (session["current_conversation_id"], user_id)).fetchone()
        if conv:
            return session["current_conversation_id"]

    cursor = db.execute("INSERT INTO conversations (user_id, title) VALUES (?, ?)",
                        (user_id, f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}") )
    new_conv_id = cursor.lastrowid
    db.commit()
    return new_conv_id

# --- Flask Routes ---
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400

    if create_user(username, password):
        return jsonify({"success": True, "message": "Signup successful!"})
    return jsonify({"success": False, "message": "Username already exists."})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    remember_me = data.get("remember_me", False)

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400

    uid = verify_user(username, password)
    if uid:
        session["user_id"] = uid
        if remember_me:
            session.permanent = True
            app.permanent_session_lifetime = timedelta(hours=24)
        else:
            session.permanent = False 

        session["current_conversation_id"] = get_or_create_default_conversation(uid)

        return jsonify({"success": True, "message": "Login successful!"})
    return jsonify({"success": False, "message": "Invalid credentials."})

@app.route("/logout", methods=["POST"])
def logout():
    user_id = session.get("user_id")
    current_conv_id = session.get("current_conversation_id")
    db = get_db()

    if user_id and current_conv_id:
        conv_check = db.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?",
                                (current_conv_id, user_id)).fetchone()
        if conv_check:
            message_count = db.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
                                    (current_conv_id,)).fetchone()[0]
            if message_count == 0:
                db.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?",
                        (current_conv_id, user_id))
                db.commit()
                print(f"DEBUG: Deleted empty conversation (on logout): {current_conv_id} for user: {user_id}")

    session.pop("user_id", None)
    session.pop("current_conversation_id", None)
    return jsonify({"success": True, "message": "Logged out successfully!"})

@app.route("/check_login_status", methods=["GET"])
def check_login_status():
    if "user_id" in session:
        return jsonify({"logged_in": True})
    return jsonify({"logged_in": False})

@app.route("/new_conversation", methods=["POST"])
def new_conversation():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."})

    user_id = session["user_id"]
    db = get_db()

    current_conv_id = session.get("current_conversation_id")
    if current_conv_id:
        conv_check = db.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?",
                                (current_conv_id, user_id)).fetchone()
        if conv_check:
            message_count = db.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
                                    (current_conv_id,)).fetchone()[0]
            if message_count == 0:
                db.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?",
                        (current_conv_id, user_id))
                db.commit()
                print(f"DEBUG: Deleted empty conversation (on new chat): {current_conv_id} for user: {user_id}")
        else:
            session.pop("current_conversation_id", None)

    cursor = db.execute("INSERT INTO conversations (user_id, title) VALUES (?, ?)",
                        (user_id, f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}") )
    new_conv_id = cursor.lastrowid
    db.commit()
    
    session["current_conversation_id"] = new_conv_id
    return jsonify({"success": True, "message": "New conversation started!", "conversation_id": new_conv_id})

@app.route("/get_current_chat_history", methods=["GET"])
def get_current_chat_history():
    if "user_id" not in session:
        return jsonify({"success": False, "history": [], "current_conversation_id": None})

    user_id = session["user_id"]
    db = get_db()

    current_conv_id = session.get("current_conversation_id")
    if not current_conv_id:
        current_conv_id = get_or_create_default_conversation(user_id)
        session["current_conversation_id"] = current_conv_id

    messages = db.execute("SELECT message, response, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                          (current_conv_id,)).fetchall()
    
    history = []
    for m in messages:
        ts = datetime.strptime(m["timestamp"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M") 
        user_msg = f"[{ts}] {m['message']}"
        bot_resp = f"[{ts}] {m['response']}"
        history.append([user_msg, bot_resp])

    return jsonify({"success": True, "history": history, "current_conversation_id": current_conv_id})

@app.route("/get_conversations", methods=["GET"])
def get_conversations():
    if "user_id" not in session:
        return jsonify({"success": False, "conversations": []})

    user_id = session["user_id"]
    db = get_db()
    conversations_raw = db.execute(
        """
        SELECT c.id,
               MIN(m.timestamp) AS first_message_timestamp,
               (SELECT message FROM messages WHERE conversation_id = c.id ORDER BY timestamp ASC LIMIT 1) AS first_message_content
        FROM conversations c
        JOIN messages m ON c.id = m.conversation_id
        WHERE c.user_id = ?
        GROUP BY c.id
        HAVING COUNT(m.id) > 0 -- Only include conversations with at least one message
        ORDER BY first_message_timestamp DESC
        """,
        (user_id,)
    ).fetchall()

    conv_list = []
    for conv in conversations_raw:
        # Format the display title: "YYYY-MM-DD HH:MM - First message snippet..."
        first_msg_ts = datetime.strptime(conv["first_message_timestamp"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
        
        preview_text = conv["first_message_content"]
        if preview_text:
            preview_text = preview_text[:30] + "..." if len(preview_text) > 30 else preview_text
        else:
            preview_text = "No messages yet (Error)" # Should not happen with HAVING COUNT > 0

        display_title = f"{first_msg_ts} - {preview_text}"
        
        conv_list.append({"id": conv["id"], "title": display_title, "preview": preview_text}) # 'preview' is still useful for debugging or future expansion
    
    return jsonify({"success": True, "conversations": conv_list})

@app.route("/load_conversation/<int:conversation_id>", methods=["GET"])
def load_conversation(conversation_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in first."})
    
    user_id = session["user_id"]
    db = get_db()

    current_conv_id = session.get("current_conversation_id")
    if current_conv_id and current_conv_id != conversation_id:
        conv_check = db.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?",
                                (current_conv_id, user_id)).fetchone()
        if conv_check:
            message_count = db.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
                                    (current_conv_id,)).fetchone()[0]
            if message_count == 0:
                db.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?",
                        (current_conv_id, user_id))
                db.commit()
                print(f"DEBUG: Deleted empty conversation (on switch): {current_conv_id} for user: {user_id}")
        else:
            session.pop("current_conversation_id", None)

    conv = db.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?",
                      (conversation_id, user_id)).fetchone()
    if not conv:
        return jsonify({"success": False, "message": "Conversation not found or unauthorized."})

    session["current_conversation_id"] = conversation_id
    messages = db.execute("SELECT message, response, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                          (conversation_id,)).fetchall()
    
    history = []
    for m in messages:
        ts = datetime.strptime(m["timestamp"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
        user_msg = f"[{ts}] {m['message']}"
        bot_resp = f"[{ts}] {m['response']}"
        history.append([user_msg, bot_resp])

    return jsonify({"success": True, "history": history, "conversation_id": conversation_id})

@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"success": False, "response": "Please log in first."})
    
    user_id = session["user_id"]
    data = request.json
    new_user_msg = data.get("message")
    
    if not new_user_msg:
        return jsonify({"success": False, "response": "Message cannot be empty."}), 400

    db = get_db()

    if "current_conversation_id" not in session or not session["current_conversation_id"]:
        session["current_conversation_id"] = get_or_create_default_conversation(user_id)
    
    current_conv_id = session["current_conversation_id"]

    try:
        historical_messages = db.execute("SELECT message, response FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                                         (current_conv_id,)).fetchall()
        
        messages_for_groq = []
        for h_msg in historical_messages:
            messages_for_groq.append({"role": "user", "content": h_msg["message"]})
            messages_for_groq.append({"role": "assistant", "content": h_msg["response"]})
        
        messages_for_groq.append({"role": "user", "content": new_user_msg})

        reply = ask_groq(messages_for_groq)
        
        db.execute(
            "INSERT INTO messages (conversation_id, user_id, message, response) VALUES (?, ?, ?, ?)",
            (current_conv_id, user_id, new_user_msg, reply)
        )
        db.commit()

        # Update conversation title (if it's still the default) for potential future uses, though UI now uses first message
        current_title_row = db.execute("SELECT title FROM conversations WHERE id = ?", (current_conv_id,)).fetchone()
        if current_title_row:
            current_title = current_title_row["title"]
            if current_title.startswith("Chat ") and len(new_user_msg) > 0:
                new_title = new_user_msg[:20] + "..." if len(new_user_msg) > 20 else new_user_msg
                db.execute("UPDATE conversations SET title = ? WHERE id = ?", (new_title, current_conv_id))
                db.commit()

        return jsonify({"success": True, "response": reply})
    except Exception as e:
        db.rollback()
        print(f"Error during chat processing: {e}")
        return jsonify({"success": False, "response": f"Error processing message: {e}"})

if __name__ == "__main__":
    app.run(debug=True)