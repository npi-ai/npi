from npiai.core.base import App
from npiai_proto import api_pb2


class Discord(App):

    def __init__(self, npi_endpoint: str = None):
        super().__init__(
            app_name="discord",
            app_type=api_pb2.DISCORD,
            endpoint=npi_endpoint,
        )
