import pydantic
from fastapi import FastAPI

pg = FastAPI()


class ChatRequest(pydantic.BaseModel):
    thread_id: str



@pg.post("/chat/{app}")
async def chat(app: str):
    pass


@pg.get("/getAppScreen/{app}")
async def get_app_screen(app: str):
    pass
