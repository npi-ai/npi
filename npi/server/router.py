"""the http server for NPI backend"""

from pydantic import BaseModel
from fastapi import APIRouter

from npi.app import google
from npi.core.context import Thread

router = APIRouter()


class ChatRequest(BaseModel):
    """the payload for chat request"""
    app: str
    instruction: str
    thread_id: str | None = None


@router.post("/chat")
async def chat(req: ChatRequest):
    """the core api of NPI"""
    if req.app == "gmail":
        return req
    if req.app == "google-calendar":
        gc = google.GoogleCalendar()
        ctx = Thread()
        resp = gc.chat(message=req.instruction, context=ctx)
        return resp

    return "Error: App not found"
