import logging
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)


class JobService:
    """Service for handling background jobs like document ingestion."""
    
    @staticmethod
    async def ingest_documents(file_paths: List[str] = None) -> Dict[str, Any]:
        """
        Ingest documents from specified file paths into the vector database.
        
        Args:
            file_paths: List of file paths to ingest. If None, ingests from default data directory.
            
        Returns:
            Dictionary with ingestion status and results.
        """
        try:
            from app.services.rag_service import collection
            from app.services.embedding import get_embeddings
            
            logger.info("Starting document ingestion job")
            
            if file_paths is None:
                # Default to chunks from data directory
                try:
                    with open("./chunks/demo_chunks.json", "r") as f:
                        chunks = json.load(f)
                except FileNotFoundError:
                    logger.warning("No demo chunks found, using empty list")
                    chunks = []
            else:
                chunks = []
                for file_path in file_paths:
                    try:
                        with open(file_path, "r") as f:
                            chunks.extend(json.load(f))
                    except FileNotFoundError:
                        logger.warning(f"File not found: {file_path}")
            
            if not chunks:
                logger.info("No chunks to ingest")
                return {"status": "completed", "ingested": 0}
            
            # Get embeddings for chunks
            texts = [chunk.get("text", "") for chunk in chunks]
            embeddings = get_embeddings(texts)
            
            # Add to collection
            collection.add(
                embeddings=embeddings,
                metadatas=[{"source": chunk.get("source", "unknown")} for chunk in chunks],
                documents=texts,
                ids=[str(i) for i in range(len(chunks))]
            )
            
            logger.info(f"Successfully ingested {len(chunks)} documents")
            return {
                "status": "completed",
                "ingested": len(chunks),
                "message": f"Successfully ingested {len(chunks)} documents"
            }
            
        except Exception as e:
            logger.error(f"Error during document ingestion: {str(e)}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
