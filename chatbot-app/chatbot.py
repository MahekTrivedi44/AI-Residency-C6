import requests

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

def ask_groq(messages):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile", # Ensure this model is available or use another suitable one
        "messages": messages
    }
    response = requests.post(GROQ_ENDPOINT, headers=headers, json=data)
    response.raise_for_status() # Raise an exception for HTTP errors
    return response.json()['choices'][0]['message']['content']
