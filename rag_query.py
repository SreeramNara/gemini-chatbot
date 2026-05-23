import os
from google import genai
import chromadb

# ---------------------------
# SINGLE EMBEDDING CLIENT
# ---------------------------
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ---------------------------
# SINGLE CHROMA INSTANCE
# ---------------------------
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="cloudrun_docs")


def get_embedding(text: str):
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        print("[EMBEDDING ERROR]", str(e))
        return None


def retrieve_chunks(query: str, k: int = 5):
    query_embedding = get_embedding(query)

    if not query_embedding:
        return [], []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    print(f"\n[DEBUG] Retrieved {len(docs)} chunks for query: {query}")

    return docs, metas


def debug_retrieval(query: str, k: int = 10):
    docs, metas = retrieve_chunks(query, k)

    print("\n================ DEBUG RETRIEVAL ================")

    for i, (doc, meta) in enumerate(zip(docs, metas)):
        print(f"\n[{i}] SOURCE: {meta.get('source')} | chunk {meta.get('chunk_id')}")
        print(f"TEXT PREVIEW: {doc[:200]}")

    print("==================================================\n")

    return {
        "documents": [docs],
        "metadatas": [metas]
    }