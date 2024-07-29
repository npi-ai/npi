from typing import Type
import json
import signal
import sys
import re

import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from npiai.core.tool._function import BaseTool
from npiai.context import Context


class Container:
    def __init__(self, tool_cls: Type[BaseTool]):
        self.tool_cls = tool_cls

    def schemas(self):
        obj = self.tool_cls()
        print(obj.schema())

    def run(self, port: int = 19140):
        app = FastAPI()

        @app.api_route(
            "/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        async def root(full_path: str, request: Request):
            # ctx = Context.from_request(req=request)
            ctx = Context()
            tool = ctx.get_tool()
            if tool is None:
                tool = self.tool_cls.from_context(ctx=ctx)
                await tool.start()

            try:
                ctx.entry()
                method = self.convert_camel_to_snake(full_path)
                match request.method:
                    case "POST":
                        args = await request.json()
                    case "GET":
                        args = {k: v for k, v in request.query_params.items()}
                    case _:
                        return JSONResponse(
                            {"error": "Method not allowed"}, status_code=405
                        )
                res = await tool.exec(ctx, method, args)
                return JSONResponse(
                    content=json.loads(res),
                    headers={
                        "X-Context-Id": ctx.id,
                    },
                )
            except Exception as e:
                logging.error(f"Failed to process request: {e}", exc_info=True)
                return JSONResponse({"error": f"internal error: {e}"}, status_code=500)
            finally:
                ctx.exit()

        def signal_handler(sig, frame):
            print(f"Signal {sig} received, shutting down...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        # signal.signal(signal.SIGKILL, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        uvicorn.run(app, host="0.0.0.0", port=port)

    @staticmethod
    def convert_camel_to_snake(name: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


if __name__ == "__main__":
    from npiai.tools import GitHub

    container = Container(GitHub)
    container.run()
