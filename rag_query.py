import os
from google import genai
import chromadb

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="cloudrun_docs")


def get_embedding(text: str):
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return response.embeddings[0].values


def retrieve_chunks(question: str, k=5):
    query_embedding = get_embedding(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )

    return results["documents"][0], results["metadatas"][0]


def ask(question: str):
    docs, metas = retrieve_chunks(question)

    context = "\n\n".join(
        f"[Source: {m['source']}]\n{d}"
        for d, m in zip(docs, metas)
    )

    prompt = f"""
You are a Cloud Run documentation assistant.

RULES:
- Only use the context below
- If answer is not in context, say: "I don't have information on that in the Cloud Run docs."

Context:
{context}

Question:
{question}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    return response.text


if __name__ == "__main__":
    while True:
        q = input("\nAsk a Cloud Run question: ")
        print("\n" + ask(q))