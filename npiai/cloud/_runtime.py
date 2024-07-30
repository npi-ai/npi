import os
import asyncio
import sys
import re
import json
import logging
import signal
from typing import List

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from npiai import utils
from npiai.context import ContextManager
from npiai.core.base import BaseTool

from ._context import CloudContext
from ._client import Client


class ToolRuntime:
    def __init__(
        self,
        tool_cls: List[BaseTool.__class__],
        port: int = 9140,
        endpoint="https://api.npi.ai",
    ):
        self.tools = {}
        self._endpoint = endpoint
        for tool in tool_cls:
            self.tools[tool.name] = tool
        self.port = port
        self.app = FastAPI()
        self.ctx_mgr = ContextManager()

    def run(self):
        self._start()

    def get_tool(self, name: str) -> BaseTool.__class__:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")

        return self.tools[name]

    def _start(self):
        """Start the server"""
        if not utils.is_cloud_env():
            raise RuntimeError(
                "Server mode is disabled, if you want to run the server, set env NPIAI_SERVICE_MODE=true"
            )

        def convert_camel_to_snake(name: str) -> str:
            return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

        @self.app.api_route(
            "/{tool_name}/{full_path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        )
        async def root(request: Request, tool_name: str, full_path: str):
            method = convert_camel_to_snake(full_path)
            try:
                ssid = request.headers.get("x-npi-session-id")
                if not ssid:
                    authorization = request.headers.get("authorization")
                    token = authorization.split(" ")
                    access_token = ""
                    if (
                        len(token) == 2 and token[0].lower() == "bearer"
                    ):  # TODO apikey & none auth?
                        access_token = token[1]
                    ctx = CloudContext(
                        req=request,
                        client=Client(
                            access_token=access_token, endpoint=self._endpoint
                        ),
                    )
                    self.ctx_mgr.save_context(ctx)
                else:
                    ctx = self.ctx_mgr.get_context(ssid)
                    if not ctx:
                        raise HTTPException(
                            status_code=404, detail="session context not found"
                        )
                tool_cls = self.get_tool(tool_name)
                async with tool_cls.from_context(ctx) as instance:
                    match request.method:
                        case "POST":
                            args = await request.json()
                            res = await instance.exec(ctx, method, args)
                        case "GET":
                            args = {k: v for k, v in request.query_params.items()}
                            res = await instance.exec(ctx, method, args)
                        case _:
                            return JSONResponse(
                                {"error": "Method not allowed"}, status_code=405
                            )
                    try:
                        return JSONResponse(content=json.loads(res))
                    except json.JSONDecodeError as e:
                        return res
            except Exception as e:
                logging.error(f"Failed to process request: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Internal Server Error")

        def signal_handler(sig, frame):
            print(f"Signal {sig} received, shutting down...")
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:  # 'RuntimeError: There is no current event loop...'
                loop = None

            # tsk = loop.create_task(self.end())
            # while not tsk.done():
            #     time.sleep(1)
            print("Shutdown complete")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        # signal.signal(signal.SIGKILL, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        for tool in self.tools.values():
            logging.info(f"the tool:{tool.get_name()} has started", exc_info=True)
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
