import os
import sys
import importlib
import tokenize
import asyncio
import sleep

async def main():
    # Add the directory containing the file to sys.path
    module_dir, module_name = os.path.split(os.environ.get('MAIN_FILE'))
    module_name = os.path.splitext(module_name)[0]  # Remove the .py extension

    if module_dir not in sys.path:
        sys.path.append(module_dir)

    # Now you can import the module using its name
    module = importlib.import_module(module_name)
    # Create an instance of the class
    tool_class = getattr(module, os.environ.get('MAIN_CLASS'))
    instance = tool_class()

    async with instance as i:
        # await i.wait() TODO add this method to BaseApp class
        sleep(1000)


if __name__ == '__main__':
    asyncio.run(main())