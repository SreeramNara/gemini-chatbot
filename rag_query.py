import os
from google import genai
import chromadb

# Embedding client
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

def debug_retrieval(query: str, k=10):
    results = collection.query(
        query_embeddings=[get_embedding(query)],
        n_results=k
    )

    print("\n================ DEBUG RETRIEVAL ================")

    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        print(f"\n[{i}] SOURCE: {meta['source']} | chunk {meta['chunk_id']}")
        print(f"DISTANCE: {dist}")
        print(f"TEXT PREVIEW: {doc[:200]}")

    print("==================================================\n")

    return results

def retrieve_chunks(query, k=5):
    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )

    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []

    # DEBUG (important while fixing)
    print("\n[DEBUG] Retrieved docs:", len(docs))

    return docs, metas