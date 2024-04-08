"""the http server for NPI backend"""

from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter()


class ChatRequest(BaseModel):
    """the payload for chat request"""
    app: str
    task: str
    thread_id: str


@router.post("/chat")
async def chat(req: ChatRequest):
    """the core api of NPI"""
    return req
