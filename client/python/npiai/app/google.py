from client.python.npiai.core.base import App


class Calendar(App):

    def __init__(self, npi_endpoint: str = None):
        super().__init__(app_name="google_calendar", endpoint=npi_endpoint)


class Gmail(App):

    def __init__(self, npi_endpoint: str = None):
        super().__init__(app_name="gmail", endpoint=npi_endpoint)
