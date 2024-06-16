import os
import sys
import importlib
import time
import asyncio
import json


def print_tool_spec():
    # Add the directory containing the file to sys.path
    module_dir, module_name = os.path.split('%s')
    module_name = os.path.splitext(module_name)[0]  # Remove the .py extension

    if module_dir not in sys.path:
        sys.path.append(module_dir)

    # Now you can import the module using its name
    module = importlib.import_module(module_name)
    # Create an instance of the class
    tool_class = getattr(module, '%s')
    instance = tool_class()
    print(json.dumps(instance.export()))


async def main():
    # Add the directory containing the file to sys.path
    module_dir, module_name = os.path.split('app.py')
    module_name = os.path.splitext(module_name)[0]  # Remove the .py extension

    if module_dir not in sys.path:
        sys.path.append(module_dir)

    # Now you can import the module using its name
    module = importlib.import_module(module_name)
    # Create an instance of the class
    tool_class = getattr(module, 'GitHub')
    instance = tool_class()

    async with instance as i:
        # await i.wait() TODO add this method to BaseApp class
        time.sleep(1000)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'spec':
            print_tool_spec()
        elif sys.argv[1] == 'server':
            asyncio.run(main())
        else:
            print('Usage: python entrypoint.py spec|server')
            sys.exit(1)
    else:
        print('Usage: python entrypoint.py spec|server')
        sys.exit(1)
