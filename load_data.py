import uuid
from datetime import datetime

from app.utils.chunking import chunk_text
from app.services.embedding import get_embeddings
from app.services.vectordb import collection


# 🔥 Source documents
texts = [
    {
        "file_name": "fastapi",
        "content": "FastAPI is a modern web framework for building APIs with Python.",
        "category": "framework"
    },
    {
        "file_name": "rag",
        "content": "RAG stands for Retrieval Augmented Generation.",
        "category": "genai"
    },
    {
        "file_name": "chromadb",
        "content": "ChromaDB is a vector database used to store embeddings.",
        "category": "database"
    },
    {
        "file_name": "embeddings",
        "content": "Embeddings convert text into numerical vectors for similarity search.",
        "category": "ai"
    },
    {
        "file_name": "python",
        "content": "Python is a versatile programming language loved by developers.",
        "category": "programming"
    },
    {
        "file_name": "javascript",
        "content": "JavaScript is essential for web development and runs in the browser.",
        "category": "programming"
    },
    {
        "file_name": "java",
        "content": "Java is a popular programming language used for building enterprise applications.",
        "category": "programming"
    },
]


all_chunks = []
all_embeddings = []
all_ids = []
all_metadata = []


print("🚀 Starting data ingestion...\n")


# 🔥 Process documents
for item in texts:

    print(f"📄 Processing: {item['file_name']}")

    # Step 1: Chunking
    chunks = chunk_text(
        text=item["content"],
        file_name=item["file_name"]
    )

    if not chunks:
        print(f"⚠️ No chunks created for {item['file_name']}")
        continue

    # Step 2: Embeddings
    embeddings = get_embeddings(chunks)

    # 🔥 Process documents
for item in texts:

    print(f"📄 Processing: {item['file_name']}")

    # Step 1: Chunking
    chunks = chunk_text(
        text=item["content"],
        file_name=item["file_name"]
    )

    # Step 2: Embeddings
    embeddings = get_embeddings(chunks)

   
    # Step 3: Build metadata
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):

        unique_id = str(uuid.uuid4())

        metadata = {
            "source": item["file_name"],
            "category": item["category"],
            "chunk_index": idx,
            "created_at": datetime.utcnow().isoformat()
        }

        all_chunks.append(chunk)
        all_embeddings.append(embedding)
        all_ids.append(unique_id)
        all_metadata.append(metadata)

    print(f"✅ {len(chunks)} chunks processed\n")

# =========================================
# SAVE EMBEDDINGS TO FILE
# =========================================

import os
import json

os.makedirs("embeddings", exist_ok=True)

embedding_data = []

for idx, (chunk, embedding) in enumerate(zip(all_chunks, all_embeddings)):

    embedding_data.append({
        "chunk_id": all_ids[idx],
        "text": chunk,
        "embedding": embedding
    })

with open("embeddings/embeddings.json", "w", encoding="utf-8") as f:
    json.dump(embedding_data, f, indent=4)

print("✅ Embeddings stored successfully")

# 🔥 Store in ChromaDB
if all_chunks:

    collection.add(
        documents=all_chunks,
        embeddings=all_embeddings,
        ids=all_ids,
        metadatas=all_metadata
    )

    print("🎉 Data stored successfully in ChromaDB")

    print(f"""
📊 Summary
-------------------
Documents : {len(texts)}
Chunks    : {len(all_chunks)}
Embeddings: {len(all_embeddings)}
""")

else:
    print("❌ No data available for storage")