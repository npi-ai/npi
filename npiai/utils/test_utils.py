from npiai import Context
from npiai.types import RuntimeMessage
from npiai.utils import logger


class DebugContext(Context):
    async def send(self, msg: RuntimeMessage):
        if msg["type"] == "screenshot":
            return
        logger.info(msg["message"] if "message" in msg else msg)
