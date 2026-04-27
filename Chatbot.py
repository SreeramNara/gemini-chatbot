import os
import gradio as gr
from google import genai

# API client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# System persona
SYSTEM_PERSONALITY = "You are Shakespeare. Speak in poetic, old-English style."

# Conversation memory
history = []

def chat(user_message):
    global history

    # Check for bad input
    if not user_message.strip():
        return "Please enter a message."

    # Add user message to memory
    history.append(f"User: {user_message}")

    try:
        prompt = SYSTEM_PERSONALITY + "\n\n" + "\n".join(history)

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )

        reply = response.text

        # Add Gemini response to memory
        history.append(f"Gemini: {reply}")

        return reply

    except Exception as e:
        return f"Error: {str(e)}"


# Gradio UI
interface = gr.Interface(
    fn=chat,
    inputs="text",
    outputs="text",
    title="Gemini Chatbot",
    description="Chat with Gemini"
)

interface.launch()