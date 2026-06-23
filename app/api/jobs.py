from fastapi import APIRouter, BackgroundTasks
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs")

@router.post("/ingest")
async def ingest(background_tasks: BackgroundTasks):

    background_tasks.add_task(
        JobService.ingest_documents
    )

    return {
        "status": "started"
    }