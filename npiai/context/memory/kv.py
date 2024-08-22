from typing import Dict, TYPE_CHECKING

from npiai.utils import logger
from .base import BaseMemory

if TYPE_CHECKING:
    from npiai.context import Context


class KVMemory(BaseMemory):
    # TODO: connect to DB
    _storage: Dict[str, str] = {}

    async def _ask_human(self, key: str):
        """
        Ask human if no memory is found

        Args:
            key: Property key
        """

        value = await self._ctx.hitl.input(
            ctx=self._ctx,
            tool_name="KV Storage",
            message=f"Please provide the following information: {key}",
        )

        await self.save(key, value)

    async def save(self, key: str, value: str):
        """
        Save the given information into KV memory

        Args:
            key: Property key
            value: Property value
        """
        self._storage[key] = value

    async def get(
        self,
        key: str,
        _is_retry: bool = False,
    ) -> str:
        """
        Search the KV storage for information

        Args:
            key: Property key
            _is_retry: Retry flag
        """

        async def retry():
            if _is_retry:
                return

            # invoke HITL and retry
            await self._ask_human(key)
            return await self.get(key, _is_retry=True)

        value = self._storage.get(key, None)

        if not value:
            logger.info(f"No property found for key: {key}")
            return await retry()

        return value
