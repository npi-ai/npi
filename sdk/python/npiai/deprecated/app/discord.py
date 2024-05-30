from npiai.deprecated.core import App
from npiai_proto import api_pb2
from typing_extensions import override


class Discord(App):
    __access_token: str

    def __init__(self, access_token: str, **kwargs):
        super().__init__(
            app_name="discord",
            app_type=api_pb2.DISCORD,
            **kwargs,
        )

        self.__access_token = access_token

    @override
    def authorize(self):
        super()._authorize(credentials={"access_token": self.__access_token})