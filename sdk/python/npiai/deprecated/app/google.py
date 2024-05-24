from npiai.deprecated.core import App
from npiai_proto import api_pb2
from typing_extensions import override


class GoogleApp(App):
    _secrets: str
    _auth_app_name: str
    _redirect_uri: str

    @override
    def authorize(self):
        super()._authorize(
            credentials={
                "app": self._auth_app_name,
                "secrets": self._secrets,
                "callback": self._redirect_uri,
            }
        )


class Calendar(GoogleApp):
    def __init__(self, secrets: str, redirect_uri: str, **kwargs):
        super().__init__(
            app_name="google_calendar",
            app_type=api_pb2.GOOGLE_CALENDAR,
            **kwargs,
        )

        self._auth_app_name = "calendar"
        self._secrets = secrets
        self._redirect_uri = redirect_uri


class Gmail(App):
    def __init__(self, secrets: str, redirect_uri: str, **kwargs):
        super().__init__(
            app_name="gmail",
            app_type=api_pb2.GOOGLE_GMAIL,
            **kwargs,
        )

        self._auth_app_name = "gmail"
        self._secrets = secrets
        self._redirect_uri = redirect_uri
