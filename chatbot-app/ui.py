# ui.py
import gradio as gr
import requests
import time
import re
from datetime import datetime

API_URL = "http://127.0.0.1:5000"
session = requests.Session()

# Helper function to format history for Gradio Chatbot (type='messages')
def _format_history_for_chatbot(history_list_of_lists):
    """Converts history from [[user_msg, bot_reply], ...] to [{'role': 'user', 'content': user_msg}, {'role': 'assistant', 'content': bot_reply}, ...]."""
    formatted_history = []
    for user_msg, bot_reply in history_list_of_lists:
        formatted_history.append({"role": "user", "content": user_msg})
        formatted_history.append({"role": "assistant", "content": bot_reply})
    return formatted_history

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
    try:
        r = session.post(f"{API_URL}/signup", json={"username": username, "password": password})
        r.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return r.json()["message"]
    except requests.exceptions.ConnectionError:
        return "Failed to connect to the backend server. Please ensure app.py is running."
    except requests.exceptions.JSONDecodeError:
        return "Backend returned an unreadable response. Check app.py console for errors."
    except requests.exceptions.RequestException as e:
        return f"An error occurred during signup: {e}"

def log_in(username, password, remember_me):
    try:
        r = session.post(f"{API_URL}/login", json={"username": username, "password": password, "remember_me": remember_me})
        r.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        result = r.json()
        message = result["message"]
        success = result["success"]

        # First yield: Update status message, keep auth_ui visible, clear chat states explicitly
        yield (
            gr.update(visible=True), 
            gr.update(visible=False), 
            message, 
            gr.update(value=[]), # Clear chatbot
            gr.update(value=None), # Clear current_conversation_id_state
            gr.update(choices=[], value=None) # Clear dropdown
        )
        
        time.sleep(1) # Reduced delay for quicker feedback

        if success:
            # Upon successful login, fetch the current chat history and conversation list
            current_chat_r = session.get(f"{API_URL}/get_current_chat_history")
            current_chat_r.raise_for_status()
            current_chat_result = current_chat_r.json()
            chat_history = current_chat_result.get("history", [])
            conv_id = current_chat_result.get("current_conversation_id")
            
            conversations_r = session.get(f"{API_URL}/get_conversations")
            conversations_r.raise_for_status()
            conversations_result = conversations_r.json()
            conv_list_data = conversations_result.get("conversations", [])
            
            # This format is (display_label, actual_value)
            conv_dropdown_choices = [(f"{c['title']} ({c['preview']})", c['id']) for c in conv_list_data]

            # Determine the value to set for the dropdown
            # Only set conv_id if it's actually in the list of choices
            dropdown_selected_value = conv_id if any(c['id'] == conv_id for c in conv_list_data) else None

            # Format chat history for the chatbot
            formatted_chat_history = _format_history_for_chatbot(chat_history)

            # Second yield: Transition to chat_ui and populate states
            yield (
                gr.update(visible=False), 
                gr.update(visible=True), 
                "", # Clear status message
                gr.update(value=formatted_chat_history), # Update chatbot with history in new format
                gr.update(value=conv_id), # Set current_conversation_id_state
                # Ensure choices are set before value to prevent "Value not in choices" error
                gr.update(choices=conv_dropdown_choices, value=dropdown_selected_value) # Update and select in dropdown
            )
        else:
            # If login fails, keep auth_ui, clear chat states explicitly
            yield (
                gr.update(visible=True), # auth_ui visible
                gr.update(visible=False), # chat_ui hidden
                gr.update(value=""), # Clear status (or show specific error message)
                gr.update(value=[]), # Clear chatbot
                gr.update(value=None), # Clear current_conversation_id_state
                gr.update(choices=[], value=None) # Clear dropdown
            )
    
    except requests.exceptions.ConnectionError:
        yield (
            gr.update(visible=True), gr.update(visible=False), 
            "Failed to connect to the backend server. Please ensure app.py is running.", 
            gr.update(value=[]), gr.update(value=None), gr.update(choices=[], value=None)
        )
    except requests.exceptions.JSONDecodeError:
        yield (
            gr.update(visible=True), gr.update(visible=False), 
            "Backend returned an unreadable response. Check app.py console for errors.", 
            gr.update(value=[]), gr.update(value=None), gr.update(choices=[], value=None)
        )
    except requests.exceptions.RequestException as e:
        yield (
            gr.update(visible=True), gr.update(visible=False), 
            f"An error occurred during login: {e}", 
            gr.update(value=[]), gr.update(value=None), gr.update(choices=[], value=None)
        )


def log_out():
    try:
        r = session.post(f"{API_URL}/logout")
        r.raise_for_status()
        message = r.json()["message"]
        return (
            gr.update(visible=True), gr.update(visible=False), message, 
            gr.update(value=[]), gr.update(value=None), gr.update(choices=[], value=None)
        )
    except requests.exceptions.ConnectionError:
        return (
            gr.update(visible=True), gr.update(visible=False), "Failed to connect to backend on logout. Please ensure app.py is running.", 
            gr.update(value=[]), gr.update(value=None), gr.update(choices=[], value=None)
        )
    except requests.exceptions.JSONDecodeError:
        return (
            gr.update(visible=True), gr.update(visible=False), "Backend returned unreadable response on logout. Check app.py console.", 
            gr.update(value=[]), gr.update(value=None), gr.update(choices=[], value=None)
        )
    except requests.exceptions.RequestException as e:
        return (
            gr.update(visible=True), gr.update(visible=False), f"An error occurred during logout: {e}", 
            gr.update(value=[]), gr.update(value=None), gr.update(choices=[], value=None)
        )


def chat_with_bot(msg, history):
    try:
        # history parameter will already be in the 'messages' format if chatbot is type='messages'
        # Add user message to history
        history.append({"role": "user", "content": msg})

        r = session.post(f"{API_URL}/chat", json={"message": msg})
        r.raise_for_status()
        reply = r.json()["response"]
        
        # Add bot reply to history
        history.append({"role": "assistant", "content": reply})
        return gr.update(value=""), gr.update(value=history) # Use gr.update for consistency
    except requests.exceptions.ConnectionError:
        gr.Warning("Could not connect to backend. Please ensure app.py is running.")
        return gr.update(), gr.update() # Use gr.update() instead of gr.no_change()
    except requests.exceptions.JSONDecodeError:
        gr.Warning("Backend returned an unreadable response. Check app.py console for errors.")
        return gr.update(), gr.update() # Use gr.update() instead of gr.no_change()
    except requests.exceptions.RequestException as e:
        gr.Warning(f"An error occurred during chat: {e}")
        return gr.update(), gr.update() # Use gr.update() instead of gr.no_change()


def start_new_chat():
    try:
        r = session.post(f"{API_URL}/new_conversation")
        r.raise_for_status()
        if r.json()["success"]:
            new_conv_id = r.json()["conversation_id"]
            
            conv_r = session.get(f"{API_URL}/get_conversations")
            conv_r.raise_for_status()
            conv_list_data = conv_r.json()["conversations"]
            conv_dropdown_choices = [(f"{c['title']} ({c['preview']})", c['id']) for c in conv_list_data]
            
            # Determine the value to set for the dropdown
            dropdown_selected_value = new_conv_id if any(c['id'] == new_conv_id for c in conv_list_data) else None

            return (
                gr.update(value=[]), # Clear chatbot (empty list is valid for type='messages')
                gr.update(value=new_conv_id), # Set new current_conversation_id_state
                gr.update(choices=conv_dropdown_choices, value=dropdown_selected_value) # Update dropdown and select new chat
            )
        gr.Error("Failed to start new chat.")
        return gr.update(), gr.update(), gr.update() # Use gr.update() instead of gr.no_change()
    except requests.exceptions.ConnectionError:
        gr.Warning("Could not connect to backend to start new chat. Ensure app.py is running.")
        return gr.update(), gr.update(), gr.update() # Use gr.update() instead of gr.no_change()
    except requests.exceptions.JSONDecodeError:
        gr.Warning("Backend returned unreadable response for new chat. Check app.py console.")
        return gr.update(), gr.update(), gr.update() # Use gr.update() instead of gr.no_change()
    except requests.exceptions.RequestException as e:
        gr.Warning(f"An error occurred starting new chat: {e}")
        return gr.update(), gr.update(), gr.update() # Use gr.update() instead of gr.no_change()

def load_selected_conversation(conversation_id_from_dropdown):
    if not conversation_id_from_dropdown:
        # If nothing is selected (e.g., dropdown cleared), reset chat
        return gr.update(value=[]), gr.update(value=None), gr.update() # Use gr.update() instead of gr.no_change()

    try:
        r = session.get(f"{API_URL}/load_conversation/{conversation_id_from_dropdown}")
        r.raise_for_status()
        if r.json()["success"]:
            loaded_history = r.json()["history"]
            # Format loaded history for the chatbot
            formatted_loaded_history = _format_history_for_chatbot(loaded_history)
            return (
                gr.update(value=formatted_loaded_history), # Update chatbot with history in new format
                gr.update(value=conversation_id_from_dropdown), # Set current_conversation_id_state
                gr.update() # Use gr.update() instead of gr.no_change() - Dropdown doesn't need update if already selected
            )
        gr.Error("Failed to load conversation.")
        return gr.update(), gr.update(), gr.update() # Use gr.update() instead of gr.no_change()
    except requests.exceptions.ConnectionError:
        gr.Warning("Could not connect to backend to load conversation. Ensure app.py is running.")
        return gr.update(), gr.update(), gr.update() # Use gr.update() instead of gr.no_change()
    except requests.exceptions.JSONDecodeError:
        gr.Warning("Backend returned unreadable response for loading conversation. Check app.py console.")
        return gr.update(), gr.update(), gr.update() # Use gr.update() instead of gr.no_change()
    except requests.exceptions.RequestException as e:
        gr.Warning(f"An error occurred loading conversation: {e}")
        return gr.update(), gr.update(), gr.update() # Use gr.update() instead of gr.no_change()

# Initial check for login status on Gradio UI load
def check_initial_login_status():
    try:
        r = session.get(f"{API_URL}/check_login_status")
        r.raise_for_status()
        result = r.json()
        if result.get("logged_in"):
            current_chat_r = session.get(f"{API_URL}/get_current_chat_history")
            current_chat_r.raise_for_status()
            current_chat_result = current_chat_r.json()
            chat_history = current_chat_result.get("history", [])
            conv_id = current_chat_result.get("current_conversation_id")
            
            conversations_r = session.get(f"{API_URL}/get_conversations")
            conversations_r.raise_for_status()
            conversations_result = conversations_r.json()
            conv_list_data = conversations_result.get("conversations", [])
            conv_dropdown_choices = [(f"{c['title']} ({c['preview']})", c['id']) for c in conv_list_data]

            # Determine the value to set for the dropdown
            dropdown_selected_value = conv_id if any(c['id'] == conv_id for c in conv_list_data) else None

            # Format chat history for the chatbot
            formatted_chat_history = _format_history_for_chatbot(chat_history)

            return (
                gr.update(visible=False), # auth_ui hidden
                gr.update(visible=True),  # chat_ui visible
                gr.update(value=""),                   # Clear status message
                gr.update(value=formatted_chat_history),          # Load chatbot history in new format
                gr.update(value=conv_id),               # Set current_conversation_id_state
                gr.update(choices=conv_dropdown_choices, value=dropdown_selected_value) # Update and select in dropdown
            )
        else:
            return (
                gr.update(visible=True),  # auth_ui visible
                gr.update(visible=False), # chat_ui hidden
                gr.update(value=""),                   # Clear status
                gr.update(value=[]),                   # Clear chatbot (empty list is valid for type='messages')
                gr.update(value=None),                 # Clear current_conversation_id_state
                gr.update(choices=[], value=None) # Clear dropdown
            )
    except requests.exceptions.ConnectionError:
        return (
            gr.update(visible=True), gr.update(visible=False), 
            "Could not connect to backend server. Please ensure app.py is running.", 
            gr.update(value=[]), gr.update(value=None), gr.update(choices=[], value=None)
        )
    except requests.exceptions.JSONDecodeError:
        return (
            gr.update(visible=True), gr.update(visible=False), 
            "Backend returned an unreadable response on load. Check app.py console for errors.", 
            gr.update(value=[]), gr.update(value=None), gr.update(choices=[], value=None)
        )
    except requests.exceptions.RequestException as e:
        return (
            gr.update(visible=True), gr.update(visible=False), 
            f"An error occurred on initial load: {e}", 
            gr.update(value=[]), gr.update(value=None), gr.update(choices=[], value=None)
        )


with gr.Blocks(css="style.css") as demo:
    gr.Markdown("<h1 style='color:#cc66cc;'>💖 Welcome to GroqBot!</h1>")

    # Gradio State components to hold dynamic values
    current_conversation_id_state = gr.State(None) # Defined here for consistency in outputs
    
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
            password_strength_feedback = gr.Markdown("")
            signup_btn = gr.Button("Sign Up")
        
        status_out = gr.Textbox(label="Status", interactive=False)

    with gr.Column(visible=False) as chat_ui:
        with gr.Row():
            with gr.Column(scale=1): # Left sidebar for chat history
                gr.Markdown("<h3 style='color:#9966cc;'>Past Chats</h3>")
                conversation_dropdown = gr.Dropdown(label="Select a Chat", choices=[], interactive=True, value=None) # Set initial value to None
                new_chat_button = gr.Button("➕ New Chat")
            with gr.Column(scale=3): # Main chat area
                gr.Markdown("<h2 style='color:#9966cc;'>💬 Chat with GroqBot</h2>")
                # Added type='messages' to address the UserWarning
                chatbot = gr.Chatbot(label="GroqBot Chat", height=400, type='messages') 
                msg = gr.Textbox(label="Your message")
                with gr.Row():
                    send_btn = gr.Button("Send")
                    logout_btn = gr.Button("Logout")

    # Client-side password strength feedback
    pass_su.change(fn=is_strong_password_client, inputs=pass_su, outputs=password_strength_feedback)

    # Login button logic
    login_btn.click(
        fn=log_in, 
        inputs=[user_li, pass_li, remember_me_li], 
        outputs=[auth_ui, chat_ui, status_out, chatbot, current_conversation_id_state, conversation_dropdown]
    )
    
    # Signup button logic
    signup_btn.click(fn=sign_up, inputs=[user_su, pass_su], outputs=status_out)

    # Send message logic
    send_btn.click(fn=chat_with_bot, inputs=[msg, chatbot], outputs=[msg, chatbot])
    msg.submit(fn=chat_with_bot, inputs=[msg, chatbot], outputs=[msg, chatbot]) # Allow Enter key to send

    # New Chat button logic
    new_chat_button.click(
        fn=start_new_chat, 
        inputs=[], 
        outputs=[chatbot, current_conversation_id_state, conversation_dropdown]
    )

    # Load conversation from dropdown selection
    conversation_dropdown.change(
        fn=load_selected_conversation,
        inputs=[conversation_dropdown],
        outputs=[chatbot, current_conversation_id_state, conversation_dropdown]
    )

    # Logout functionality
    logout_btn.click(
        fn=log_out, 
        inputs=[], 
        outputs=[auth_ui, chat_ui, status_out, chatbot, current_conversation_id_state, conversation_dropdown]
    )

    # Initial load of the Gradio page to check login status and populate initial chat/conversations
    demo.load(
        fn=check_initial_login_status,
        inputs=[],
        outputs=[auth_ui, chat_ui, status_out, chatbot, current_conversation_id_state, conversation_dropdown]
    )

demo.launch()