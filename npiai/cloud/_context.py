from typing import Dict

from npiai.context import Context
from npiai.cloud import Client


class CloudContext(Context):

    def __init__(self, req, client: Client | None = None):
        if not client:
            client = Client(access_token=req.headers.get("x-npi-access-token"))
        super().__init__()
        self.client = client

    def credentials(self, app_code: str) -> Dict[str, str]:
        return self.client.get_credentials(app_code)
