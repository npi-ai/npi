import asyncio
import os
from typing import Dict, TypedDict
from fastapi import WebSocket

from npiai.context import Context
from npiai.cloud import Client
from npiai.types import RuntimeMessage


class ActionResult(TypedDict):
    action_id: str
    result: str


class CloudContext(Context):
    ws: WebSocket | None
    action_result_queue: asyncio.Queue[ActionResult]

    def __init__(self, req, client: Client | None = None):
        if not client:
            client = Client(access_token=req.headers.get("x-npi-access-token"))
        super().__init__()
        self.client = client
        self.ws = None
        self.action_result_queue = asyncio.Queue()

    def attach_websocket(self, websocket: WebSocket):
        self.ws = websocket

    def detach_websocket(self):
        self.ws = None

    async def send(self, msg: RuntimeMessage) -> None:
        if self.ws is not None:
            await self.ws.send_json(msg)

        await super().send(msg)

    async def put_action_result(self, result: ActionResult):
        await self.action_result_queue.put(result)

    async def receive_action_result(self, action_id: str) -> str:
        while True:
            msg = await self.action_result_queue.get()
            if msg.get("action_id", None) == action_id:
                return msg.get("result", "No result provided")

    def credentials(self, app_code: str) -> Dict[str, str]:
        return self.client.get_credentials(app_code)
