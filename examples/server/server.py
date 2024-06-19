import os

from npiai.app import GitHub

os.environ.setdefault("NPIAI_TOOL_SERVER_MODE", "true")
instance = GitHub(access_token="123")
instance.server()
