from npiai.core.base import App
from npiai_proto import api_pb2


class Browser(App):

    def __init__(self, npi_endpoint: str = None):
        super().__init__(
            app_name="browser",
            app_type=api_pb2.WEB_BROWSER,
            endpoint=npi_endpoint,
        )
