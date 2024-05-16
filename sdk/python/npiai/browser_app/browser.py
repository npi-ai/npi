from npiai.core.base import BrowserApp
from npiai_proto import api_pb2


class Browser(BrowserApp):

    def __init__(self, **kwargs):
        super().__init__(
            app_name="browser",
            app_type=api_pb2.WEB_BROWSER,
            **kwargs,
        )
