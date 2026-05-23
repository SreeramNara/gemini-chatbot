import os
import time
import gradio as gr
from google import genai
from google.genai.errors import ServerError

from rag_query import retrieve_chunks


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def call_gemini(prompt: str) -> str:
    models = [
        "gemini-2.5-flash-lite",
        "gemini-1.5-flash"
    ]

    for model in models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                return response.text

            except ServerError:
                time.sleep(2 ** attempt)

            except Exception:
                break

    return "Model is temporarily unavailable. Please try again."


def respond(message, history):
    docs, metas = retrieve_chunks(message)

    if not docs:
        context = "No relevant Cloud Run documentation found."
        sources = []
    else:
        context = "\n\n".join(docs)
        sources = [
            f"{m.get('source', 'unknown')} (chunk {m.get('chunk_id', '?')})"
            for m in metas
        ]

    prompt = f"""
You are a Cloud Run documentation assistant.

RULES:
- Only use the provided context
- If not found, say you don't know

Context:
{context}

Question:
{message}
"""

    response = call_gemini(prompt)

    if sources:
        response += "\n\nSources:\n" + "\n".join(sources)

    return response


demo = gr.ChatInterface(fn=respond)

demo.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7860))
)