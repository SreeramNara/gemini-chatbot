import os
import gradio as gr
from google import genai

client = None

def get_client():
    global client
    if client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise Exception("Missing GEMINI_API_KEY")
        client = genai.Client(api_key=key)
    return client

SYSTEM_PERSONALITY = "You are Shakespeare. Speak in poetic, old-English style."

history = []

def chat(user_message):
    global history

    if not user_message or not user_message.strip():
        return "Please enter a message."

    history.append(f"User: {user_message}")

    try:
        prompt = SYSTEM_PERSONALITY + "\n\n" + "\n".join(history)

        c = get_client()

        response = c.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )

        reply = response.text

        history.append(f"Assistant: {reply}")

        return reply

    except Exception as e:
        return f"Error: {str(e)}"

interface = gr.Interface(
    fn=chat,
    inputs=gr.Textbox(label="Your message"),
    outputs=gr.Textbox(label="Response"),
    title="Gemini Chatbot",
    description="Chat with Gemini (Shakespeare mode)"
)

print("STARTING APP...")
print("PORT:", os.environ.get("PORT"))
print("API KEY EXISTS:", bool(os.getenv("GEMINI_API_KEY")))

interface.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 8080))
)