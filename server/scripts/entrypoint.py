import os
import sys
import importlib
import time
import asyncio
import json

from npiai.runtime import ToolRuntime

tool_file = "/Users/wenfeng/workspace/npi-ai/npi/npiai/tools/github/app.py"
tool_main_class = "GitHub"


def print_tool_spec():
    # Add the directory containing the file to sys.path
    module_dir, module_name = os.path.split(tool_file)
    module_name = os.path.splitext(module_name)[0]  # Remove the .py extension

    if module_dir not in sys.path:
        sys.path.append(module_dir)

    # Now you can import the module using its name
    module = importlib.import_module(module_name)
    # Create an instance of the class
    tool_class = getattr(module, tool_main_class)
    instance = tool_class()
    print(json.dumps(instance.schema()))


def main():
    # Add the directory containing the file to sys.path
    module_dir, module_name = os.path.split(tool_file)
    module_name = os.path.splitext(module_name)[0]  # Remove the .py extension

    if module_dir not in sys.path:
        sys.path.append(module_dir)

    # Now you can import the module using its name
    module = importlib.import_module(module_name)
    tool_class = getattr(module, tool_main_class)
    runtime = ToolRuntime(tool_cls=[tool_class], port=9141)
    asyncio.run(runtime.run())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "spec":
            print_tool_spec()
        elif sys.argv[1] == "server":
            print("Starting server...")
            main()
        else:
            print("Usage: python entrypoint.py spec|server")
            sys.exit(1)
    else:
        print("Usage: python entrypoint.py spec|server")
        sys.exit(1)
