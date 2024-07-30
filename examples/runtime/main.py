import asyncio
import os

from npiai.cloud import ToolRuntime
from npiai.tools import GitHub, Gmail

if __name__ == "__main__":
    os.environ.setdefault("NPIAI_SERVICE_MODE", 'True')

    runtime = ToolRuntime(tool_cls=[GitHub, Gmail], port=9141)
    asyncio.run(runtime.run())
