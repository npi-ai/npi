import asyncio
import os

from npiai.cloud import ToolRuntime
from npiai.tools import GitHub, Gmail
from npiai.tools.web import Chromium

if __name__ == "__main__":
    os.environ.setdefault("NPIAI_SERVICE_MODE", "True")

    runtime = ToolRuntime(
        tool_cls=[GitHub, Gmail, Chromium],
        port=9141,
        endpoint="https://api.npiai.dev",
    )
    asyncio.run(runtime.run())
