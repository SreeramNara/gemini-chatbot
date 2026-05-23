import os
import uuid
from google import genai
import chromadb
from pypdf import PdfReader
import hashlib


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

def get_file_hash(path):
    hasher = hashlib.md5()

    with open(path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)

    return hasher.hexdigest()

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
    docs = load_documents()

    print(f"Loaded {len(docs)} chunks")

    existing = collection.get()

    existing_ids = set()

    if existing["metadatas"]:
        for meta in existing["metadatas"]:
            source = meta["source"]
            chunk_id = meta["chunk_id"]

            existing_ids.add(f"{source}_{chunk_id}")

    added = 0
    skipped = 0

    for doc in docs:
        unique_id = f"{doc['source']}_{doc['chunk_id']}"

        if unique_id in existing_ids:
            skipped += 1
            continue

        embedding = get_embedding(doc["text"])

        collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            documents=[doc["text"]],
            metadatas=[{
                "source": doc["source"],
                "chunk_id": doc["chunk_id"]
            }]
        )

        added += 1

    print(f"Added {added} new chunks")
    print(f"Skipped {skipped} existing chunks")

    return {
        "chunks_loaded": len(docs),
        "new_chunks_added": added,
        "existing_chunks_skipped": skipped
    }

def ingest_single_file(path, original_filename):
    file_hash = get_file_hash(path)

    existing = collection.get(where={"source": original_filename})

    metadatas = existing.get("metadatas") or []

    # Extract ALL hashes from existing chunks
    existing_hashes = {
        meta.get("file_hash")
        for meta in metadatas
        if meta.get("file_hash")
    }

    # If file exists AND hash matches → skip
    if file_hash in existing_hashes and len(existing_hashes) == 1:
        return {
            "message": "File already exists unchanged",
            "new_chunks_added": 0
        }

    # Always delete old version before re-ingest
    collection.delete(where={"source": original_filename})

    content = extract_text(path)

    if not content:
        raise Exception("Could not extract text from file")

    chunks = chunk_text(content)

    added = 0

    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()

        if len(chunk) < 50:
            continue

        embedding = get_embedding(chunk)

        collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{
                "source": original_filename,
                "chunk_id": i,
                "file_hash": file_hash
            }]
        )

        added += 1

    return {
        "message": "File re-ingested successfully",
        "new_chunks_added": added
    }