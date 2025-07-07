import gradio as gr
import requests
import time
import re # Import regex for client-side password validation

API_URL = "http://127.0.0.1:5000"
session = requests.Session()

# Client-side password strength check for real-time feedback
def is_strong_password_client(password):
    strength = {
        "length": len(password) >= 8,
        "uppercase": bool(re.search(r"[A-Z]", password)),
        "lowercase": bool(re.search(r"[a-z]", password)),
        "number": bool(re.search(r"\d", password)),
        "special": bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))
    }
    feedback = []
    if not strength["length"]: feedback.append("Min 8 characters")
    if not strength["uppercase"]: feedback.append("Uppercase letter")
    if not strength["lowercase"]: feedback.append("Lowercase letter")
    if not strength["number"]: feedback.append("Number")
    if not strength["special"]: feedback.append("Special character")
    
    if all(strength.values()):
        return "<p style='color:green'>Strong password!</p>"
    else:
        return f"<p style='color:red'>Password needs: {', '.join(feedback)}</p>"

def sign_up(username, password):
    r = session.post(f"{API_URL}/signup", json={"username": username, "password": password})
    return r.json()["message"]

def log_in(username, password, remember_me):
    r = session.post(f"{API_URL}/login", json={"username": username, "password": password, "remember_me": remember_me})
    result = r.json()
    message = result["message"]
    success = result["success"]

    # First yield: Update only the status message, keep auth_ui visible
    yield gr.update(visible=True), gr.update(visible=False), message, [] # Also clear chatbot
    
    # Introduce a delay here to let the user read the message
    time.sleep(1) 

    # Second yield: After the delay, perform the UI redirection if successful
    if success:
        # Fetch chat history after successful login
        history_r = session.get(f"{API_URL}/get_chat_history")
        chat_history = []
        if history_r.json()["success"]:
            chat_history = history_r.json()["history"]

        yield gr.update(visible=False), gr.update(visible=True), "", chat_history
    else:
        yield gr.update(), gr.update(), "", [] # Keep current visibility, clear message, clear history

def log_out():
    r = session.post(f"{API_URL}/logout")
    message = r.json()["message"]
    return gr.update(visible=True), gr.update(visible=False), message, [] # Show auth, hide chat, show message, clear chat

def chat_with_bot(msg, history):
    # history comes as a list of lists: [[user_msg1, bot_reply1], [user_msg2, bot_reply2], ...]
    # The backend expects a list of dictionaries with "user" and "bot" keys for history.
    # However, the chatbot component manages the display directly.
    # When sending to backend, we convert the Gradio chat history format to the API's expected format.
    
    # The history sent to the backend needs to be in the format: [{"role": "user", "content": "..."}] and [{"role": "assistant", "content": "..."}]
    # Gradio's chat history is [[user_msg, bot_reply], ...]
    
    r = session.post(f"{API_URL}/chat", json={"message": msg, "history": history})
    reply = r.json()["response"]
    
    # Append the new message and reply to the history for the Gradio chatbot
    history.append([msg, reply])
    return "", history # Clear message box, return updated history

#Login status check function to run on app start
def check_initial_login_status():
    try:
        r = session.get(f"{API_URL}/check_login_status")
        result = r.json()
        if result.get("logged_in"):
            # If logged in, fetch chat history
            history_r = session.get(f"{API_URL}/get_chat_history")
            chat_history = []
            if history_r.json()["success"]:
                chat_history = history_r.json()["history"]
            
            # Hide auth_ui, show chat_ui, and load history
            return gr.update(visible=False), gr.update(visible=True), "", chat_history
        else:
            # Not logged in, keep auth_ui visible
            return gr.update(visible=True), gr.update(visible=False), "", []
    except requests.exceptions.ConnectionError:
        # Handle case where backend might not be running
        return gr.update(visible=True), gr.update(visible=False), "Could not connect to backend. Please ensure the server is running.", []
    except Exception as e:
        return gr.update(visible=True), gr.update(visible=False), f"An error occurred: {e}", []

with gr.Blocks(css="style.css") as demo:
    gr.Markdown("<h1 style='color:#cc66cc;'>💖 Welcome to GroqBot!</h1>")

    with gr.Column(visible=True) as auth_ui:
        gr.Markdown("🌸 Sign up or log in to begin chatting with your cute AI friend.")
        
        with gr.Tab("Log In"):
            user_li = gr.Textbox(label="Username")
            pass_li = gr.Textbox(label="Password", type="password")
            remember_me_li = gr.Checkbox(label="Remember me for 24 hours")
            login_btn = gr.Button("Log In")
        
        with gr.Tab("Sign Up"):
            user_su = gr.Textbox(label="Username")
            pass_su = gr.Textbox(label="Password", type="password")
            password_strength_feedback = gr.Markdown("") # To display password strength feedback
            signup_btn = gr.Button("Sign Up")
        
        status_out = gr.Textbox(label="Status", interactive=False)

    with gr.Column(visible=False) as chat_ui:
        gr.Markdown("<h2 style='color:#9966cc;'>💬 Chat with GroqBot</h2>")
        chatbot = gr.Chatbot(label="GroqBot Chat", height=400) # Use gr.Chatbot
        msg = gr.Textbox(label="Your message")
        with gr.Row():
            send_btn = gr.Button("Send")
            new_chat_btn = gr.Button("New Chat") # New Chat button
            logout_btn = gr.Button("Logout") # Logout button

    # Client-side password strength feedback
    pass_su.change(fn=is_strong_password_client, inputs=pass_su, outputs=password_strength_feedback)

    login_btn.click(fn=log_in, inputs=[user_li, pass_li, remember_me_li], 
                    outputs=[auth_ui, chat_ui, status_out, chatbot]) # Add chatbot to outputs for initial history

    signup_btn.click(fn=sign_up, inputs=[user_su, pass_su], 
                      outputs=status_out)

    send_btn.click(fn=chat_with_bot, inputs=[msg, chatbot], outputs=[msg, chatbot])
    
    # Clear chat history for a new chat
    new_chat_btn.click(lambda: gr.update(value=[]), outputs=chatbot)

    # Logout functionality
    logout_btn.click(fn=log_out, inputs=[], outputs=[auth_ui, chat_ui, status_out, chatbot])
    demo.load(
        fn=check_initial_login_status,
        inputs=[],
        outputs=[auth_ui, chat_ui, status_out, chatbot]
    )
demo.launch()