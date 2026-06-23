from pydantic import BaseModel

class PushCodeRequest(BaseModel):
    branch_name: str
    commit_message: str