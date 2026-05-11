from app.services.embedding import get_embeddings
import chromadb
import ollama
import re
from typing import List, Dict, Any

# =========================================
# Configuration
# =========================================

OLLAMA_MODEL = "llama3.2"

TOP_K = 3

SIMILARITY_THRESHOLD = 0.7


# =========================================
# ChromaDB Setup
# =========================================

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="rag_collection"
)


# =========================================
# Query Cleaning
# =========================================

def clean_query(query: str) -> str:

    query = query.lower()

    remove_phrases = [
        "in 100 words",
        "explain",
        "describe",
        "tell me about",
        "briefly",
        "summarize"
    ]

    for phrase in remove_phrases:
        query = query.replace(phrase, "")

    query = re.sub(r"\s+", " ", query).strip()

    return query


# =========================================
# Filter Relevant Documents
# =========================================

def filter_relevant_docs(
    docs: List[str],
    distances: List[float],
    threshold: float
) -> List[Dict[str, Any]]:

    filtered = []

    for doc, dist in zip(docs, distances):

        if dist <= threshold:

            filtered.append({
                "text": doc,
                "distance": round(dist, 4)
            })

    return filtered


# =========================================
# Remove Duplicate Chunks
# =========================================

def remove_duplicates(docs):

    seen = set()

    unique_docs = []

    for item in docs:

        if item["text"] not in seen:

            seen.add(item["text"])

            unique_docs.append(item)

    return unique_docs


# =========================================
# Main RAG Function
# =========================================

def get_rag_response(query: str):

    try:

        # ---------------------------------
        # Step 1: Clean Query
        # ---------------------------------

        cleaned_query = clean_query(query)

        # ---------------------------------
        # Step 2: Generate Embedding
        # ---------------------------------

        query_embedding = get_embeddings(
            [cleaned_query]
        )[0]

    except Exception as e:

        return {
            "error": f"Embedding generation failed: {str(e)}"
        }

    try:

        # ---------------------------------
        # Step 3: Retrieve Documents
        # ---------------------------------

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K
        )

    except Exception as e:

        return {
            "error": f"Vector DB query failed: {str(e)}"
        }

    docs = results.get("documents", [[]])[0]

    distances = results.get("distances", [[]])[0]

    # ---------------------------------
    # No Results
    # ---------------------------------

    if not docs:

        return {
            "response": {
                "question": query,
                "answer": "I don't know."
            }
        }

    # ---------------------------------
    # Step 4: Threshold Filtering
    # ---------------------------------

    filtered_docs = filter_relevant_docs(
        docs,
        distances,
        SIMILARITY_THRESHOLD
    )

    # ---------------------------------
    # Keyword Fallback
    # ---------------------------------

    if not filtered_docs:

        query_words = cleaned_query.split()

        for doc in docs:

            if any(
                word in doc.lower()
                for word in query_words
            ):

                filtered_docs.append({
                    "text": doc,
                    "distance": 1.0
                })

    # ---------------------------------
    # Still No Results
    # ---------------------------------

    if not filtered_docs:

        return {
            "response": {
                "question": query,
                "answer": "I don't know."
            }
        }

    # ---------------------------------
    # Step 5: Remove Duplicates
    # ---------------------------------

    filtered_docs = remove_duplicates(
        filtered_docs
    )

    # ---------------------------------
    # Step 6: Build Context
    # ---------------------------------

    context = "\n\n".join([
        item["text"]
        for item in filtered_docs[:3]
    ])

    # ---------------------------------
    # Step 7: Prompt Engineering
    # ---------------------------------

    system_prompt = """
You are an enterprise-grade RAG assistant.

STRICT RULES:
1. Answer ONLY using provided context.
2. NEVER use outside knowledge.
3. NEVER hallucinate.
4. NEVER make assumptions.
5. If answer is unavailable, respond:
   "I don't know."
6. Keep answers concise and factual.
7. Return ONLY the answer text.
"""

    user_prompt = f"""
Context:
{context}

Question:
{query}
"""

    try:

        # ---------------------------------
        # Step 8: Generate Response
        # ---------------------------------

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        final_answer = response.get(
            "message",
            {}
        ).get(
            "content",
            ""
        ).strip()

        if not final_answer:

            final_answer = "I don't know."

        # ---------------------------------
        # Step 9: Structured Response
        # ---------------------------------

        return {
            "response": {
                "question": query,
                "answer": final_answer,
                "retrieved_chunks": len(filtered_docs),
                "confidence_threshold": SIMILARITY_THRESHOLD,
                "sources": [
                    item["text"]
                    for item in filtered_docs[:2]
                ]
            }
        }

    except Exception as e:

        return {
            "error": f"Ollama generation failed: {str(e)}"
        }