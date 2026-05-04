import os
import gradio as gr
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

chat = client.chats.create(model="gemini-2.5-flash-lite")

def respond(message, history):
    response = chat.send_message(message)
    return response.text

demo = gr.ChatInterface(fn=respond)

demo.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 8080))
)