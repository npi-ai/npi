import asyncio
import os

from npiai.tools import GitHub
from npiai.runtime import ToolRuntime


if __name__ == "__main__":
    os.environ.setdefault("NPIAI_SERVICE_MODE", 'True')
    runtime = ToolRuntime(tool_cls=[GitHub])
    asyncio.run(runtime.run())
