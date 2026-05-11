import re
import os
import json


def chunk_text(text, file_name="sample"):
    
    # Create chunks folder
    os.makedirs("chunks", exist_ok=True)

    # Clean text
    text = re.sub(r'\s+', ' ', text).strip()

    # Split text into chunks
    chunk_size = 300
    overlap = 50

    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    # JSON data
    chunk_data = []

    for idx, chunk in enumerate(chunks, start=1):
        chunk_data.append({
            "chunk_id": idx,
            "text": chunk
        })

    # File path
    output_path = f"chunks/{file_name}_chunks.json"

    # Save file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunk_data, f, indent=4, ensure_ascii=False)

    print(f"Chunks stored successfully: {output_path}")

    return chunks