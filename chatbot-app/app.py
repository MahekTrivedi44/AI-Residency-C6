from flask import Flask, request, session, jsonify
from flask_cors import CORS
from auth import create_user, verify_user
from chatbot import ask_groq
from db import init_db, get_db

app = Flask(__name__)
app.secret_key = "supercutesecret"
CORS(app, supports_credentials=True)

init_db()

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    if create_user(data["username"], data["password"]):
        return jsonify({"success": True, "message": "Signup successful!"})
    return jsonify({"success": False, "message": "Username already exists."})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    uid = verify_user(data["username"], data["password"])
    if uid:
        session["user_id"] = uid
        return jsonify({"success": True, "message": "Login successful!"})
    return jsonify({"success": False, "message": "Invalid credentials."})

@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"success": False, "response": "Please log in first."})
    
    data = request.json
    msg = data["message"]
    reply = ask_groq(msg)
    db = get_db()
    db.execute("INSERT INTO messages (user_id, message, response) VALUES (?, ?, ?)",
               (session["user_id"], msg, reply))
    db.commit()
    return jsonify({"success": True, "response": reply})

if __name__ == "__main__":
    app.run(debug=True)
