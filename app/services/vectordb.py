import uuid

import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="rag_collection")


def store_documents(chunks, embeddings):
    ids = [str(uuid.uuid4()) for _ in chunks]

    collection.upsert(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
    )


def query_db(query_embedding):
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
    )
    return results["documents"][0]
