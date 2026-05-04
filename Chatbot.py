import os
import gradio as gr
from google import genai

client = None
chat_session = None

def get_client():
    global client
    if client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise Exception("Missing GEMINI_API_KEY")
        client = genai.Client(api_key=key)
    return client

def get_chat():
    global chat_session
    if chat_session is None:
        c = get_client()
        chat_session = c.models.start_chat(
            model="gemini-2.5-flash-lite",
            history=[]
        )
    return chat_session

def chat(user_message, history):
    if not user_message or not user_message.strip():
        return "Please enter a message."

    try:
        chat = get_chat()
        response = chat.send_message(user_message)
        return response.text

    except Exception as e:
        return f"Error: {str(e)}"

interface = gr.ChatInterface(
    fn=chat,
    title="Gemini Chatbot",
    description="Chat with Gemini"
)

print("STARTING APP...")
print("PORT:", os.environ.get("PORT"))
print("API KEY EXISTS:", bool(os.getenv("GEMINI_API_KEY")))

interface.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 8080))
)