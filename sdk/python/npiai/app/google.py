from npiai.core.base import App
from npiai_proto import api_pb2


class Calendar(App):

    def __init__(self, npi_endpoint: str = None, npi_token: str = None):
        super().__init__(
            app_name="google_calendar",
            app_type=api_pb2.GOOGLE_CALENDAR,
            endpoint=npi_endpoint,
            npi_token=npi_token,
        )


class Gmail(App):

    def __init__(self, npi_endpoint: str = None, npi_token: str = None):
        super().__init__(
            app_name="gmail",
            app_type=api_pb2.GOOGLE_GMAIL,
            endpoint=npi_endpoint,
            npi_token=npi_token,
        )
