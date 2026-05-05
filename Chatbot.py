import os
import time
import gradio as gr
from google import genai
from google.genai.errors import ServerError

from rag_query import retrieve_chunks

# API client (Cloud Run uses Secret Manager env var)
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
                time.sleep(2 ** attempt)  # exponential backoff

            except Exception:
                # unknown error → try next model
                break

    return "Model is temporarily unavailable. Please try again."


def respond(message, history):
    docs, metas = retrieve_chunks(message)

    if not docs:
        context = "No relevant Cloud Run docs found."
        sources = []
    else:
        context = "\n\n".join(docs)

        sources = [
            f"{m['source']} (chunk {m['chunk_id']})"
            for m in metas
        ]

    prompt = f"""
You are a Cloud Run documentation assistant.

RULES:
- Only use the context below
- If not found say:
  "I don't have information on that in the Cloud Run docs."
- Do NOT guess

Context:
{context}

Question:
{message}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    ).text

    if sources:
        response += "\n\nSources:\n" + "\n".join(sources)

    return response


demo = gr.ChatInterface(fn=respond)

demo.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 8080))
)