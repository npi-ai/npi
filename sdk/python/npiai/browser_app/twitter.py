from npiai.core.base import App
from npiai_proto import api_pb2


class Twitter(App):

    def __init__(self, npi_endpoint: str = None):
        super().__init__(
            app_name="twitter",
            app_type=api_pb2.TWITTER,
            endpoint=npi_endpoint,
        )
