import os
import uuid
from google import genai
import chromadb


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


def load_documents():
    docs = []

    for filename in os.listdir(DOCS_FOLDER):
        if not filename.endswith(".txt"):
            continue

        path = os.path.join(DOCS_FOLDER, filename)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # simple split by headings (your docs already structured well)
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


if __name__ == "__main__":
    embed_and_store()