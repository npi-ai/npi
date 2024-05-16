from npiai.core.base import App
from npiai_proto import api_pb2
from typing_extensions import override


class GitHub(App):
    __access_token: str

    def __init__(self, access_token: str, **kwargs):
        super().__init__(
            app_name="github",
            app_type=api_pb2.GITHUB,
            **kwargs,
        )

        self.__access_token = access_token

    @override
    def authorize(self):
        super()._authorize(credentials={"access_token": self.__access_token})
