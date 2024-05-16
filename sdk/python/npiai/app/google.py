from npiai.core.base import App
from npiai_proto import api_pb2
from typing_extensions import override


class GoogleApp(App):
    _secret: str
    _auth_app_name: str
    _redirect_uri: str

    @override
    def authorize(self):
        super()._authorize(
            credentials={
                "app": self._auth_app_name,
                "secret": self._secret,
            }
        )


class Calendar(GoogleApp):
    def __init__(self, secret: str, redirect_uri: str, **kwargs):
        super().__init__(
            app_name="google_calendar",
            app_type=api_pb2.GOOGLE_CALENDAR,
            **kwargs,
        )

        self._auth_app_name = "calendar"
        self._secret = secret
        self._redirect_uri = redirect_uri


class Gmail(App):
    def __init__(self, secret: str, redirect_uri: str, **kwargs):
        super().__init__(
            app_name="gmail",
            app_type=api_pb2.GOOGLE_GMAIL,
            **kwargs,
        )

        self._auth_app_name = "gmail"
        self._secret = secret
        self._redirect_uri = redirect_uri
