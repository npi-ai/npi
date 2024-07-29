import base64
import json
from typing import Dict

import requests


class Client:
    __API_VERSION = "2024-07-25"

    def __init__(self, access_token, endpoint="https://api.npi.ai"):
        self._base_url = endpoint
        self._api_version = "2024-07-25"
        self._access_token = (access_token,)
        self.client = requests.Session()
        self.client.headers.update({"Content-Type": "application/json"})
        self.client.headers.update({"Accept": "application/json"})
        self.client.headers.update({"Authorization": f"Bearer {access_token}"})
        self.client.headers.update({"x-npi-api-version": self._api_version})

    @property
    def api_version(self):
        return self._api_version

    def get_credentials(self, app: str) -> Dict[str, str]:
        response = self.client.request("GET", f"{self._base_url}/credentials/{app}")
        if response.status_code != 200:
            raise Exception(f"Failed to get credentials: {response.text}")
        creds = json.loads(response.text)
        # Decoding the Base64 string
        decoded_bytes = base64.b64decode(creds["credentials"])
        return json.loads(decoded_bytes.decode("utf-8"))


if __name__ == "__main__":
    client = Client(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzIxOTM1MTg1LCJpc3MiOiJucGkuY29tIiwic3ViIjoiZ2l0aHViXzk3NjY4MjEifSwidXVpZCI6IjY2ODhhY2VhMmEwNTgxYTM2ZjQwNjkzOSIsInRvb2xfaWQiOiI2NjlkZjlhMTgxOGNlMmE2OTllOTU2ZmYiLCJjbGllbnRfaWQiOiJGelhBU2pJdVBWMlNXeW5qeHJJVCIsImhpbnQiOiI2NjllMjdlYTAwYmY2MWYzMjQ0ODFiNjUifQ.kh3D7691gwaXNBBudaWu0C46G15rsEOqsZpLEUhXYGc",
        endpoint="http://localhost:8080",
    )
    print(client.get_credentials("github"))
