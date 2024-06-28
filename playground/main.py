from pydantic import BaseModel
from fastapi import FastAPI


class ChatRequest(BaseModel):
    thread_id: str
    tool_id: str
    instruction: str
    action_id: str
    action_result: str
    pass


pg = FastAPI()


@pg.get("/getScreen")
def get_web_screen():
    pass


@pg.post("/chat")
def chat(req: ChatRequest):
    pass
