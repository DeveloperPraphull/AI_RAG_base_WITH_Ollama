from fastapi import APIRouter

from app.models.github_models import PushCodeRequest
from app.services.github_service import push_code

router = APIRouter()


@router.post("/github/push")
def github_push(
    req: PushCodeRequest
):

    return push_code(
        req.branch_name,
        req.commit_message
    )