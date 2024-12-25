import json
import os
import asyncio
from npiai.tools.outlook import Outlook
from azure.identity import InteractiveBrowserCredential


async def main():
    creds = InteractiveBrowserCredential(
        client_id=os.environ.get("AZURE_CLIENT_ID", None),
        # tenant_id=os.environ.get("AZURE_TENANT_ID", None),
        tenant_id="common",
    )

    async with Outlook(creds) as outlook:
        async for email in outlook.list_inbox_stream(limit=10):
            print(json.dumps(email, indent=4))


if __name__ == "__main__":
    asyncio.run(main())
