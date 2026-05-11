# from app.utils.chunking import chunk_text
# from app.services.embedding import get_embeddings
# from app.services.vectordb import store_documents

# text = open("data/sample.txt").read()

# chunks = chunk_text(text)
# embeddings = get_embeddings(chunks)

# store_documents(chunks, embeddings)

# print("Data loaded successfully")


from app.utils.chunking import chunk_text
from app.services.embedding import get_embeddings
from app.services.vectordb import store_documents

# 👇 Your text data as array
texts = [
    "FastAPI is a modern web framework for building APIs with Python.",
    "RAG stands for Retrieval Augmented Generation.",
    "ChromaDB is a vector database used to store embeddings.",
    "Embeddings convert text into numerical vectors for similarity search."
]

all_chunks = []

# Step 1: Chunk each text
for text in texts:
    chunks = chunk_text(text)
    all_chunks.extend(chunks)

# Step 2: Generate embeddings
embeddings = get_embeddings(all_chunks)

# Step 3: Store in vector DB
store_documents(all_chunks, embeddings)

print("Data loaded successfully")