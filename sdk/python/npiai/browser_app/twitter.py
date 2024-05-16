from npiai.core.base import BrowserApp
from npiai_proto import api_pb2
from typing_extensions import override


class Twitter(BrowserApp):
    _username: str
    _password: str

    def __init__(self, username: str, password: str, **kwargs):
        super().__init__(
            app_name="twitter",
            app_type=api_pb2.TWITTER,
            **kwargs,
        )

        self._username = username
        self._password = password

    @override
    def authorize(self):
        super()._authorize(
            credentials={
                "username": self._username,
                "password": self._password,
            }
        )
