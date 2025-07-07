import gradio as gr
import requests
import time

API_URL = "http://127.0.0.1:5000"
session = requests.Session()

def sign_up(username, password):
    r = session.post(f"{API_URL}/signup", json={"username": username, "password": password})
    return r.json()["message"]

def log_in(username, password):
    r = session.post(f"{API_URL}/login", json={"username": username, "password": password})
    result = r.json()
    message = result["message"]
    success = result["success"]

    # First yield: Update only the status message, keep auth_ui visible
    yield gr.update(visible=True), gr.update(visible=False), message
    
    # Introduce a delay here to let the user read the message
    time.sleep(2) # Adjust this duration as needed (e.g., 2 seconds)

    # Second yield: After the delay, perform the UI redirection if successful
    if success:
        yield gr.update(visible=False), gr.update(visible=True), "" # Hide auth_ui, show chat_ui, clear message
    else:
        yield gr.update(), gr.update(), "" # Keep current visibility, clear message (optional, could keep error)

def chat_with_bot(msg):
    r = session.post(f"{API_URL}/chat", json={"message": msg})
    return r.json()["response"]

with gr.Blocks(css="style.css") as demo:
    login_visible = gr.State(True)

    with gr.Column(visible=True) as auth_ui:
        gr.Markdown("<h1 style='color:#cc66cc;'>💖 Welcome to GroqBot!</h1>")
        gr.Markdown("🌸 Sign up or log in to begin chatting with your cute AI friend.")
        
        with gr.Tab("Log In"):
            user_li = gr.Textbox(label="Username")
            pass_li = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Log In")
        
        with gr.Tab("Sign Up"):
            user_su = gr.Textbox(label="Username")
            pass_su = gr.Textbox(label="Password", type="password")
            signup_btn = gr.Button("Sign Up")
        
        status_out = gr.Textbox(label="Status", interactive=False)

    with gr.Column(visible=False) as chat_ui:
        gr.Markdown("<h2 style='color:#9966cc;'>💬 Chat with GroqBot</h2>")
        msg = gr.Textbox(label="Your message")
        send = gr.Button("Send")
        reply = gr.Textbox(label="GroqBot says:", interactive=False)

    # Note: No need for .success() chaining with this approach
    login_btn.click(fn=log_in, inputs=[user_li, pass_li], 
                    outputs=[auth_ui, chat_ui, status_out])
    
    signup_btn.click(fn=sign_up, inputs=[user_su, pass_su], 
                      outputs=status_out)

    send.click(fn=chat_with_bot, inputs=msg, outputs=reply)

demo.launch()