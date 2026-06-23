from datetime import datetime, timezone
import chromadb
import requests
from fastapi import APIRouter, Query
from app.models.schema import GitPushRequest
from app.services.git_service import GitService
from app.services.rag_service import get_rag_response
from app.utils.usage_logger import log_query, read_all_logs, read_logs_for_date
from app.integrations.whatsapp import notify_search

router = APIRouter()


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@router.get("/")
def root():
    return {"message": "Welcome to the RAG API"}


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@router.post("/chat/{query}")
def chat(query: str):
    response = get_rag_response(query)
    answer = response.get("response", {}).get("answer", "") if "response" in response else ""
    log_query(query=query, answer=answer, source="api")

    try:
        notify_search(query=query, source="api", answer=answer)
    except Exception:
        pass

    return response


# ---------------------------------------------------------------------------
# Git push
# POST /git/push
# ---------------------------------------------------------------------------

@router.post("/git/push")
def git_push(request: GitPushRequest):
    try:
        GitService.check_repository()
        branch_result = GitService.create_or_switch_branch(request.branch_name)
        stage_result = GitService.stage_all()
        commit_result = GitService.commit_all(request.commit_message or "Update code")
        push_result = GitService.push_branch(request.branch_name, request.remote)
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


@router.post("/postbymcp")
def post_by_mcp(request: GitPushRequest):
    return git_push(request)


# ---------------------------------------------------------------------------
# Usage — all queries on a specific date
# GET /usage/date/2026-05-10
# GET /usage/date/today
# ---------------------------------------------------------------------------

@router.get("/usage/date/{date}")
def usage_by_date(date: str):
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
# Usage — summary stats for a specific date
# GET /usage/summary/2026-05-10
# GET /usage/summary/today
# ---------------------------------------------------------------------------

@router.get("/usage/summary/{date}")
def usage_summary(date: str):
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

    by_source: dict = {}
    hour_counts: dict = {}

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
# Usage — day-by-day history
# GET /usage/history?days=7
# ---------------------------------------------------------------------------

@router.get("/usage/history")
def usage_history(days: int = Query(default=7, ge=1, le=90)):
    all_records = read_all_logs()

    by_date: dict = {}
    for r in all_records:
        d = r.get("date", "")
        if d:
            by_date.setdefault(d, []).append(r)

    sorted_dates = sorted(by_date.keys(), reverse=True)[:days]

    return {
        "days_requested": days,
        "days_with_data": len(sorted_dates),
        "history": [
            {
                "date": d,
                "total_queries": len(by_date[d]),
                "api_queries": sum(1 for r in by_date[d] if r.get("source") == "api"),
                "mcp_queries": sum(1 for r in by_date[d] if r.get("source") == "mcp"),
            }
            for d in sorted_dates
        ],
    }


    #---------------------------------------------
    # health check endpoint
    #---------------------------------------------  



@router.get("/health")
def health():

    health = {
        "status": "UP"
    }

    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        client.list_collections()

        health["chromadb"] = "UP"

    except Exception as e:
        health["chromadb"] = f"DOWN: {e}"

    try:
        response = requests.get(
    "http://host.docker.internal:11434/api/tags",
            timeout=5
        )

        if response.status_code == 200:
            health["ollama"] = "UP"
        else:
            health["ollama"] = "DOWN"

    except Exception as e:
        health["ollama"] = f"DOWN: {e}"

    return health