from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embeddings(texts):
    embeddings = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True
    )

    return embeddings.tolist()