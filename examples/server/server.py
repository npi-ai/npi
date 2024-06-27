import os

from npiai.app import GitHub

os.environ.setdefault("NPIAI_TOOL_SERVER_MODE", "true")

# read GITHUB_ACCESS_TOKEN from environment variable
instance = GitHub()
instance.server()
