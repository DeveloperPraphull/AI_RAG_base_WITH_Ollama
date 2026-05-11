import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="rag_collection")

def store_documents(chunks, embeddings):
    for i in range(len(chunks)):
        collection.add(
            documents=[chunks[i]],
            embeddings=[embeddings[i]],
            ids=[str(i)]
        )

def query_db(query_embedding):
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )
    return results["documents"][0]