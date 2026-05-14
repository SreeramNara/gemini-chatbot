import os
import time
import gradio as gr
from google import genai
from google.genai.errors import ServerError
import chromadb

from rag_query import retrieve_chunks
from ingestion import embed_and_store


# Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Chroma DB (shared)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="cloudrun_docs")


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

    # If nothing retrieved
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
- If the answer is not in the context, say:
  "I don't have information on that in the Cloud Run docs."
- Do NOT guess

Context:
{context}

Question:
{message}
"""

    response = call_gemini(prompt)

    if sources:
        response += "\n\nSources:\n" + "\n".join(sources)

    return response


# UI
demo = gr.ChatInterface(fn=respond)

demo.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 8080))
)


if __name__ == "__main__":
    embed_and_store()