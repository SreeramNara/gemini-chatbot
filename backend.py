from fastapi import FastAPI
from pydantic import BaseModel
import traceback
import logging

from rag_query import retrieve_chunks, debug_retrieval
from ingestion import embed_and_store

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class QueryRequest(BaseModel):
    message: str


def call_gemini(prompt: str):
    from google import genai
    import os, time
    from google.genai.errors import ServerError

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    models = ["gemini-2.5-flash-lite", "gemini-1.5-flash"]

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

    return "Model unavailable"

@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: QueryRequest):
    try:
        message = req.message

        results = debug_retrieval(message)

        docs = results["documents"][0]
        metas = results["metadatas"][0]

        if not docs:
            context = "No relevant Cloud Run documentation found."
            sources = []
        else:
            context = "\n\n".join(docs)

            sources = [
                f"{m.get('source')} (chunk {m.get('chunk_id')})"
                for m in metas
            ]

        prompt = f"""
You are a Cloud Run documentation assistant.

RULES:
- Only use context below
- If not found say you don't know

Context:
{context}

Question:
{message}
"""

        response = call_gemini(prompt)

        return {
            "answer": response,
            "sources": sources
        }

    except Exception as e:
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "answer": "Internal server error"
        }
    
    
@app.post("/ingest")
def ingest():
    try:
        stats = embed_and_store()

        return {
            "status": "success",
            "message": "Documents ingested successfully",
            "stats": stats
        }

    except Exception as e:
        logger.error(traceback.format_exc())

        return {
            "status": "error",
            "message": str(e)
        }