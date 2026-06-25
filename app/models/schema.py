from typing import Optional

from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str

class GitPushRequest(BaseModel):
    branch_name: str
    commit_message: Optional[str] = "Update code"
    remote: Optional[str] = "origin"