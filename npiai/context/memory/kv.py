from typing import Dict

from npiai.utils import logger
from .base import BaseMemory


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
        ask_human: bool = True,
        _is_retry: bool = False,
    ) -> str | None:
        """
        Search the KV storage for information

        Args:
            key: Property key
            ask_human: Whether to ask human if no memory is found
            _is_retry: Retry flag
        """

        async def retry():
            if _is_retry:
                return

            # invoke HITL and retry
            await self._ask_human(key)
            return await self.get(key, _is_retry=True)

        value = self._storage.get(key, None)

        if not value and ask_human:
            logger.info(f"No property found for key: {key}")
            return await retry()

        return value

    async def delete(self, key: str):
        self._storage.pop(key, None)
