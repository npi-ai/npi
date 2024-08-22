from npiai import Context
from npiai.types import RuntimeMessage


class DebugContext(Context):
    async def send(self, msg: RuntimeMessage):
        print("Context Message:", msg)
