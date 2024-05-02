from npiai.core.base import App
from npiai_proto import api_pb2


class GitHub(App):

    def __init__(self, npi_endpoint: str = None):
        super().__init__(
            app_name="github",
            app_type=api_pb2.GITHUB,
            endpoint=npi_endpoint,
        )
