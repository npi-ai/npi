import os
import asyncio
import sys
import re
import json
import logging
import signal
from typing import Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from npiai.context import Context, ContextManager
from npiai.core.base import BaseTool


class ToolRuntime:
    def __init__(self, tool_cls: Dict[str, BaseTool.__class__], port: int = 9140):
        self.tool_cls = tool_cls
        self.port = port
        self.app = FastAPI()
        self.ctx_mgr = ContextManager()

    async def run(self):
        await self._start()

    def get_tool(self, name: str) -> BaseTool.__class__:
        if name not in self.tool_cls:
            raise ValueError(f"Tool {name} not found")

        return self.tool_cls[name]

    async def _start(self):
        """Start the server"""
        if not bool(os.environ.get("NPIAI_TOOL_SERVER_MODE")):
            print("Server mode is disabled, if you want to run the server, set env NPIAI_TOOL_SERVER_MODE=true")
            print("Exiting...")
            return

        def convert_camel_to_snake(name: str) -> str:
            return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

        @self.app.api_route("/{tool_name}/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
        async def root(request: Request, tool_name: str, full_path: str):
            method = convert_camel_to_snake(full_path)
            try:
                ctx = self.ctx_mgr.from_request(request)
                tool_cls = self.tool_cls[tool_name]
                tool = tool_cls.from_context(ctx)
                match request.method:
                    case "POST":
                        args = await request.json()
                        res = await tool.exec(ctx, method, args)
                    case "GET":
                        args = {k: v for k, v in request.query_params.items()}
                        res = await tool.exec(ctx, method, args)
                    case _:
                        return JSONResponse({'error': 'Method not allowed'}, status_code=405)
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

        uvicorn.run(self.app, host="0.0.0.0", port=self.port)