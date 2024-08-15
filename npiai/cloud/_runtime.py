import asyncio
import sys
import re
import json
import signal
from typing import List, Type

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import uvicorn

from npiai import utils
from npiai.context import ContextManager
from npiai.core.base import BaseTool

from ._context import CloudContext
from ._client import Client
from ._message import WSClientMessage, ToolCallMessage
from ._hitl import CloudHITL


def convert_camel_to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class ToolRuntime:
    def __init__(
        self,
        tool_cls: List[Type[BaseTool]],
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

    def get_tool(self, name: str) -> Type[BaseTool]:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")

        return self.tools[name]

    def _get_context(self, request: Request | WebSocket):
        ssid = request.headers.get("x-npi-session-id")

        if not ssid:
            authorization = request.headers.get("authorization")
            if not authorization:
                raise HTTPException(
                    status_code=401, detail="Missing authorization header"
                )
            token = authorization.split(" ")
            access_token = ""
            if (
                len(token) == 2 and token[0].lower() == "bearer"
            ):  # TODO apikey & none auth?
                access_token = token[1]
            ctx = CloudContext(
                client=Client(access_token=access_token, endpoint=self._endpoint),
            )
            self.ctx_mgr.save_context(ctx)
        else:
            ctx = self.ctx_mgr.get_context(ssid)
            if not ctx:
                raise HTTPException(status_code=404, detail="session context not found")

        return ctx

    def _start(self):
        """Start the server"""
        if not utils.is_cloud_env():
            raise RuntimeError(
                "Server mode is disabled, if you want to run the server, set env NPIAI_SERVICE_MODE=true"
            )

        self.app.api_route(
            "/{tool_name}/{full_path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        )(self.tool_http_endpoint)

        self.app.websocket(
            "/{tool_name}",
        )(self.tool_ws_endpoint)

        def signal_handler(sig, _frame):
            print(f"Signal {sig} received, shutting down...")
            # try:
            #     loop = asyncio.get_running_loop()
            # except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            #     loop = None

            # tsk = loop.create_task(self.end())
            # while not tsk.done():
            #     time.sleep(1)
            print("Shutdown complete")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        # signal.signal(signal.SIGKILL, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        for tool in self.tools.values():
            utils.logger.info(f"the tool:{tool.name} has started")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)

    async def tool_http_endpoint(
        self, request: Request, tool_name: str, full_path: str
    ):
        method = convert_camel_to_snake(full_path)
        try:
            ctx = self._get_context(request)
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
            utils.logger.error(e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def tool_ws_endpoint(self, ws: WebSocket, tool_name: str):
        await ws.accept()

        ctx = None

        try:
            ctx = self._get_context(ws)
            ctx.attach_websocket(ws)
            tool_cls = self.get_tool(tool_name)
            async with tool_cls.from_context(ctx) as instance:
                instance.use_hitl(CloudHITL())

                async def run_tool(call_msg: ToolCallMessage):
                    try:
                        res = await instance.exec(
                            ctx, call_msg["tool_name"], call_msg["arguments"]
                        )
                        await ctx.send_execution_result(
                            tool_call_id=call_msg["tool_call_id"], result=res
                        )
                        screenshot = await instance.get_screenshot()
                        if screenshot:
                            await ctx.send_screenshot(screenshot)
                    except Exception as e:
                        utils.logger.error(e)
                        await ctx.send_error_message(
                            f"Exception while executing {call_msg['tool_name']}: {e}"
                        )

                while True:
                    msg: WSClientMessage = await ws.receive_json()

                    match msg.get("type", None):
                        case "tool_call":
                            # run tool in parallel
                            _ = asyncio.create_task(run_tool(msg))
                        case "action_result":
                            await ctx.put_action_result(msg)
        except WebSocketDisconnect:
            if ctx:
                ctx.detach_websocket()
        except Exception as err:
            utils.logger.error(err)
            raise err
