from npiai.core.base import App
from npiai_proto import api_pb2
from typing_extensions import override


class GitHub(App):

    def __init__(self, access_token: str, npi_endpoint: str = None):
        super().__init__(
            app_name="github",
            app_type=api_pb2.GITHUB,
            endpoint=npi_endpoint,
        )
        self.access_token = access_token

    @override
    def authorize(self):
        super()._authorize(credentials={"access_token": self.access_token})
