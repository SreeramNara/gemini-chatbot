import os
import uuid
from google import genai
import chromadb
from pypdf import PdfReader

DOCS_FOLDER = "docs"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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

    # TXT + MD
    if ext in [".txt", ".md"]:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # PDF
    elif ext == ".pdf":
        reader = PdfReader(path)

        text = ""

        for page in reader.pages:
            extracted = page.extract_text()

            if extracted:
                text += extracted + "\n"

        return text

    return None


def load_documents():
    docs = []

    for filename in os.listdir(DOCS_FOLDER):
        path = os.path.join(DOCS_FOLDER, filename)

        if not os.path.isfile(path):
            continue

        content = extract_text(path)

        if not content:
            continue

        chunks = content.split("\n---\n")

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
    if collection.count() > 0:
        print("Embeddings already exist.")
        return
    
    docs = load_documents()

    print(f"Loaded {len(docs)} chunks")

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