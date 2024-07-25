import asyncio
import os
import importlib
import sys

if __name__ == "__main__":
    from npiai.cloud import ToolRuntime
    os.environ.setdefault("NPIAI_SERVICE_MODE", 'True')

    file = "{YOUR_PYTHON_TOOL_FILE}"
    module_dir, module_name = os.path.split(file)
    module_name = os.path.splitext(module_name)[0]  # Remove the .py extension

    if module_dir not in sys.path:
        sys.path.append(module_dir)

    # Now you can import the module using its name
    module = importlib.import_module(module_name)

    tool_class = getattr(module, 'GitHub')
    runtime = ToolRuntime(tool_cls=[tool_class], port=9141, endpoint='http://localhost:8080')
    asyncio.run(runtime.run())
