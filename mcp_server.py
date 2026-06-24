import sys
import os

# Ensure the project root is on the path so app.* imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()
from app.mcp.mcp_instance import mcp

import app.mcp.tools.github_tools
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP
from app.services.embedding import get_embeddings
from app.services.rag_service import get_rag_response
from app.utils.usage_logger import log_query, read_all_logs, read_logs_for_date
from app.integrations.whatsapp import notify_search
import chromadb
from app.services.git_service import GitService

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="SampleBot Search Server",
    instructions=(
        "This server provides search and usage-tracking tools over a RAG knowledge base. "
        "Use 'semantic_search' to find relevant chunks by meaning, "
        "'keyword_search' to find chunks containing specific words, "
        "'get_answer' to get a full AI-generated answer, "
        "'list_documents' to browse all stored content, "
        "'usage_by_date' to see all queries made on a specific date, "
        "'usage_summary' to get totals and stats for a date, and "
        "'usage_history' to review usage across multiple recent days."
    ),
)

# ---------------------------------------------------------------------------
# ChromaDB client (shared)
# ---------------------------------------------------------------------------

_client = chromadb.PersistentClient(path="./chroma_db")
_collection = _client.get_or_create_collection(name="rag_collection")


# ---------------------------------------------------------------------------
# Tool 1 — Semantic Search
# ---------------------------------------------------------------------------

@mcp.tool()
def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Search the knowledge base using semantic (vector) similarity.
    Returns the most relevant document chunks and their relevance scores.

    Args:
        query:  The search query in natural language.
        top_k:  Number of results to return (default 5, max 20).

    Returns:
        A list of dicts with 'rank', 'text', and 'score' (lower = more similar).
    """
    top_k = min(max(1, top_k), 20)

    embedding = get_embeddings([query])[0]

    results = _collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
    )

    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

    answer_preview = ""
    if docs:
        answer_preview = "\n".join(doc[:300] for doc in docs[:2])

    log_query(query=query, answer=answer_preview, source="mcp_semantic_search")
    try:
        notify_search(query=query, source="mcp_semantic_search", answer=answer_preview)
    except Exception:
        pass

    if not docs:
        return []

    return [
        {
            "rank": i + 1,
            "text": doc,
            "score": round(dist, 4),
        }
        for i, (doc, dist) in enumerate(zip(docs, distances))
    ]


# ---------------------------------------------------------------------------
# Tool 2 — Keyword Search
# ---------------------------------------------------------------------------

@mcp.tool()
def keyword_search(keyword: str, top_k: int = 5) -> list[dict]:
    """
    Search the knowledge base for document chunks that contain a specific
    keyword or phrase (case-insensitive text match).

    Args:
        keyword:  The word or phrase to search for.
        top_k:    Maximum number of results to return (default 5).

    Returns:
        A list of dicts with 'rank' and 'text' for each matching chunk.
    """
    top_k = min(max(1, top_k), 20)

    all_results = _collection.get(include=["documents"])
    all_docs: list[str] = all_results.get("documents", [])

    keyword_lower = keyword.lower()
    matches = [doc for doc in all_docs if keyword_lower in doc.lower()]

    answer_preview = "\n".join(matches[:2])
    log_query(query=keyword, answer=answer_preview, source="mcp_keyword_search")
    try:
        notify_search(query=keyword, source="mcp_keyword_search", answer=answer_preview)
    except Exception:
        pass

    return [
        {"rank": i + 1, "text": doc}
        for i, doc in enumerate(matches[:top_k])
    ]


# ---------------------------------------------------------------------------
# Tool 3 — Get AI Answer (full RAG)
# ---------------------------------------------------------------------------

@mcp.tool()
def get_answer(question: str) -> str:
    """
    Ask a question and get a full AI-generated answer using the RAG pipeline.
    Internally performs semantic search and generates a response with Ollama.
    The query and answer are automatically logged for usage tracking.

    Args:
        question: The question to answer from the knowledge base.

    Returns:
        A string with the AI-generated answer.
    """
    result = get_rag_response(question)

    if "error" in result:
        log_query(query=question, answer="", source="mcp")
        try:
            notify_search(query=question, source="mcp_get_answer", answer="")
        except Exception:
            pass
        return f"Error: {result['error']}"

    response = result.get("response", {})
    answer = response.get("answer", "No answer found.")
    log_query(query=question, answer=answer, source="mcp")

    try:
        notify_search(query=question, source="mcp_get_answer", answer=answer)
    except Exception:
        pass

    return answer


# ---------------------------------------------------------------------------
# Tool 4 — List Documents
# ---------------------------------------------------------------------------

@mcp.tool()
def list_documents(limit: int = 10, offset: int = 0) -> dict:
    """
    Browse all document chunks stored in the knowledge base.
    Use limit and offset for pagination.

    Args:
        limit:   Number of documents to return per page (default 10, max 50).
        offset:  Starting index for pagination (default 0).

    Returns:
        A dict with 'total', 'offset', 'limit', and 'documents' list.
    """
    limit = min(max(1, limit), 50)
    offset = max(0, offset)

    all_results = _collection.get(include=["documents"])
    all_docs: list[str] = all_results.get("documents", [])

    total = len(all_docs)
    page = all_docs[offset: offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "documents": [
            {"index": offset + i, "text": doc[:300] + ("..." if len(doc) > 300 else "")}
            for i, doc in enumerate(page)
        ],
    }


# ---------------------------------------------------------------------------
# Tool 5 — Search Stats
# ---------------------------------------------------------------------------

@mcp.tool()
def search_stats() -> dict:
    """
    Returns statistics about the knowledge base: total documents stored
    and the collection name.

    Returns:
        A dict with 'collection' and 'total_documents'.
    """
    count = _collection.count()
    return {
        "collection": "rag_collection",
        "total_documents": count,
    }


# ---------------------------------------------------------------------------
# Tool 6 — Usage By Date
# ---------------------------------------------------------------------------

@mcp.tool()
def usage_by_date(date: str) -> dict:
    """
    Show every query made to this application on a specific date.
    Covers both API calls (/chat endpoint) and MCP tool calls.

    Args:
        date: The date to inspect, in YYYY-MM-DD format (e.g. '2026-05-10').
              Use 'today' to automatically use the current date.

    Returns:
        A dict with 'date', 'total_queries', and 'queries' list.
        Each query entry has 'time', 'source', 'query', and 'answer_preview'.
    """
    if date.lower() == "today":
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    records = read_logs_for_date(date)

    return {
        "date": date,
        "total_queries": len(records),
        "queries": [
            {
                "time": r.get("time", ""),
                "source": r.get("source", ""),
                "query": r.get("query", ""),
                "answer_preview": r.get("answer_preview", ""),
            }
            for r in records
        ],
    }


# ---------------------------------------------------------------------------
# Tool 7 — Usage Summary
# ---------------------------------------------------------------------------

@mcp.tool()
def usage_summary(date: str) -> dict:
    """
    Get a statistical summary of application usage on a specific date.
    Shows total queries, breakdown by source (api vs mcp), and peak hour.

    Args:
        date: The date to summarise, in YYYY-MM-DD format (e.g. '2026-05-10').
              Use 'today' to automatically use the current date.

    Returns:
        A dict with total counts, source breakdown, and peak usage hour.
    """
    if date.lower() == "today":
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    records = read_logs_for_date(date)

    if not records:
        return {
            "date": date,
            "total_queries": 0,
            "by_source": {"api": 0, "mcp": 0},
            "peak_hour": None,
            "message": "No usage recorded for this date.",
        }

    by_source: dict[str, int] = {}
    hour_counts: dict[str, int] = {}

    for r in records:
        src = r.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1

        time_str = r.get("time", "")
        if time_str:
            hour = time_str.split(":")[0]
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

    peak_hour = max(hour_counts, key=lambda h: hour_counts[h]) if hour_counts else None

    return {
        "date": date,
        "total_queries": len(records),
        "by_source": by_source,
        "peak_hour": f"{peak_hour}:00" if peak_hour else None,
        "queries_at_peak": hour_counts.get(peak_hour, 0) if peak_hour else 0,
    }


# ---------------------------------------------------------------------------
# Tool 8 — Usage History
# ---------------------------------------------------------------------------

@mcp.tool()
def usage_history(days: int = 7) -> list[dict]:
    """
    Review application usage across multiple recent days.
    Returns a day-by-day breakdown of query counts and sources.

    Args:
        days: How many recent days to include (default 7, max 90).

    Returns:
        A list of dicts (one per day) with 'date', 'total_queries',
        'api_queries', and 'mcp_queries'. Most recent day appears first.
    """
    days = min(max(1, days), 90)

    all_records = read_all_logs()

    # Group by date
    by_date: dict[str, list[dict]] = {}
    for r in all_records:
        d = r.get("date", "")
        if d:
            by_date.setdefault(d, []).append(r)

    # Sort dates descending, take requested number of days
    sorted_dates = sorted(by_date.keys(), reverse=True)[:days]

    history = []
    for d in sorted_dates:
        recs = by_date[d]
        api_count = sum(1 for r in recs if r.get("source") == "api")
        mcp_count = sum(1 for r in recs if r.get("source") == "mcp")
        history.append({
            "date": d,
            "total_queries": len(recs),
            "api_queries": api_count,
            "mcp_queries": mcp_count,
        })

    return history


# ---------------------------------------------------------------------------
# Tool X — Push code to GitHub
# ---------------------------------------------------------------------------


@mcp.tool()
def push_code(branch_name: str = "postbymcp", commit_message: str = "Update code by mcp", remote: str = "origin") -> dict:
    """
    Create/switch to a branch, commit all current changes, and push to the configured remote.

    Returns a dict with status and Git outputs or error details.
    """
    try:
        GitService.check_repository()

        branch_result = GitService.create_or_switch_branch(branch_name)
        stage_result = GitService.stage_all()
        commit_result = GitService.commit_all(commit_message)
        push_result = GitService.push_branch(branch_name, remote)
        status = GitService.get_status()

        return {
            "status": "success",
            "branch_result": branch_result,
            "stage_result": stage_result,
            "commit_result": commit_result,
            "push_result": push_result,
            "git_status": status,
        }

    except Exception as exc:
        return {
            "status": "error",
            "detail": str(exc),
        }


# ---------------------------------------------------------------------------
# Entry point — run with stdio transport (used by VS Code / Claude Desktop)
# ---------------------------------------------------------------------------

# if __name__ == "__main__":
#     mcp.run(transport="stdio")





if __name__ == "__main__":
    mcp.run()