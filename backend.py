from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import traceback
import logging
import tempfile
import shutil
import os
import time

from ingestion import ingest_single_file
from rag_query import debug_retrieval
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai.errors import ServerError

# --------------------
# LOGGING
# --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --------------------
# CORS (PRODUCTION FIX)
# --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# GEMINI CLIENT (GLOBAL FIX)
# --------------------
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class QueryRequest(BaseModel):
    message: str

# --------------------
# GEMINI CALL
# --------------------
def call_gemini(prompt: str):
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

# --------------------
# HEALTH
# --------------------
@app.get("/")
def health():
    return {"status": "ok"}

# --------------------
# CHAT ENDPOINT
# --------------------
@app.post("/chat")
def chat(req: QueryRequest):
    try:
        message = req.message

        results = debug_retrieval(message)

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        if not docs:
            context = "No relevant documentation found."
            sources = []
        else:
            context = "\n\n".join(docs)

            sources = [
                f"{m.get('source')} (chunk {m.get('chunk_id')})"
                for m in metas
            ]

        prompt = f"""
You are a documentation assistant.

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
            "response": response,   # 🔥 FIXED (frontend now reliable)
            "sources": sources
        }

    except Exception as e:
        logger.error(traceback.format_exc())
        return {
            "response": "Internal server error",
            "error": str(e)
        }

# --------------------
# INGEST ENDPOINT
# --------------------
@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        stats = ingest_single_file(temp_path, file.filename)

        os.remove(temp_path)

        return {
            "status": "success",
            "filename": file.filename,
            "stats": stats
        }

    except Exception as e:
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": str(e)
        }