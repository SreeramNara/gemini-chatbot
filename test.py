from rag_query import retrieve_chunks

docs, metas = retrieve_chunks("What are Cloud Run revisions?")

print(docs[0])
print(metas[0])