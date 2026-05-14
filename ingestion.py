import os
import uuid
from google import genai
import chromadb
from pypdf import PdfReader


DOCS_FOLDER = "docs"

print("FILE IS RUNNING")

# Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Chroma DB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="cloudrun_docs")


def get_embedding(text: str):
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return response.embeddings[0].values


def extract_text(path):
    ext = os.path.splitext(path)[1].lower()

    # TXT / MD
    if ext in [".txt", ".md"]:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # PDF
    elif ext == ".pdf":
        reader = PdfReader(path)

        text = ""
        page_count = 0

        for page in reader.pages:
            extracted = page.extract_text()

            if extracted:
                text += extracted + "\n"
                page_count += 1

        print(f"[PDF DEBUG] {path} → pages read: {page_count}")

        if len(text.strip()) < 50:
            print(f"[WARNING] PDF ignored (too little text): {path}")

        return text

    return None


def chunk_text(text, chunk_size=1500, overlap=200):
    import re

    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current = ""

    for s in sentences:
        if len(current) + len(s) > chunk_size:
            chunks.append(current)
            current = current[-overlap:] + " " + s
        else:
            current += " " + s

    if current:
        chunks.append(current)

    return chunks


def load_documents():
    docs = []

    print("Scanning docs folder:", DOCS_FOLDER)

    for filename in os.listdir(DOCS_FOLDER):
        path = os.path.join(DOCS_FOLDER, filename)

        if not os.path.isfile(path):
            continue

        content = extract_text(path)

        if not content:
            continue

        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            chunk = chunk.strip()

            if len(chunk) < 50:
                continue

            docs.append({
                "text": chunk,
                "source": filename,
                "chunk_id": i
            })

    return docs


def embed_and_store():
    print("Clearing old embeddings...")
    collection.delete(ids=collection.get()["ids"])

    docs = load_documents()

    print(f"Loaded {len(docs)} chunks")

    if len(docs) == 0:
        print("WARNING: No documents found. Check docs folder.")
        return

    for doc in docs:
        text = doc["text"]

        embedding = get_embedding(text)

        collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "source": doc["source"],
                "chunk_id": doc["chunk_id"]
            }]
        )

    print("Done embedding and storing!")

    return {
        "chunks_loaded": len(docs)
    }


if __name__ == "__main__":
    embed_and_store()